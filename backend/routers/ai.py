from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import json
import sys
from fastapi import Query
import httpx
import requests
import time
import hashlib
import textwrap
import os
import subprocess
import boto3
from botocore.client import Config
import sys
import io
sys.stdout.reconfigure(encoding="utf-8")

router = APIRouter()
# Always use project root for past_papers dir
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# S3/Supabase config
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_BUCKET = "pdfs"

# OpenRouter (LLM) configuration
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen/qwen2.5-7b-instruct")
LLM_VISION_MODEL = os.environ.get(
    "LLM_VISION_MODEL", "qwen/qwen2.5-vl-7b-instruct"
)
LLM_FALLBACK_MODEL = os.environ.get(
    "LLM_FALLBACK_MODEL",
    "qwen/qwen2.5-3b-instruct, qwen/qwen2.5-1.5b-instruct, meta-llama/llama-3.2-3b-instruct:free",
)
LLM_CACHE_MAX = int(os.environ.get("LLM_CACHE_MAX", "50"))
LLM_REQUESTS_PER_MIN = int(os.environ.get("LLM_REQUESTS_PER_MIN", "40"))
LLM_ADAPTIVE_RETRY = os.environ.get("LLM_ADAPTIVE_RETRY", "true").lower() == "true"
LLM_ROUND_ROBIN = os.environ.get(
    "LLM_ROUND_ROBIN",
    "qwen/qwen2.5-1.5b-instruct:free, qwen/qwen2.5-3b-instruct, deepseek/deepseek-r1-distill-qwen-1.5b:free",
)
LLM_LOCAL_MODEL = os.environ.get("LLM_LOCAL_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
LLM_LOCAL_MAX_NEW_TOKENS = int(os.environ.get("LLM_LOCAL_MAX_NEW_TOKENS", "256"))
LLM_USE_LOCAL_FIRST = os.environ.get("LLM_USE_LOCAL_FIRST", "false").lower() == "true"
LLM_DISABLE_FALLBACKS = os.environ.get("LLM_DISABLE_FALLBACKS", "false").lower() == "true"
# OpenAI (preferred for this endpoint if available)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

# Simple sliding window rate limiter
_LLM_REQ_TIMESTAMPS: list[float] = []

def _rate_limit_ok() -> bool:
    now = time.time()
    cutoff = now - 60.0
    # prune
    while _LLM_REQ_TIMESTAMPS and _LLM_REQ_TIMESTAMPS[0] < cutoff:
        _LLM_REQ_TIMESTAMPS.pop(0)
    if len(_LLM_REQ_TIMESTAMPS) >= LLM_REQUESTS_PER_MIN:
        return False
    _LLM_REQ_TIMESTAMPS.append(now)
    return True

# Simple in‑memory LRU-ish cache (FIFO trim) for repeated identical prompts
_LLM_CACHE: dict[str, str] = {}
_LLM_CACHE_KEYS: list[str] = []
_LLM_RR_INDEX = 0  # simple global pointer
_LLM_COOLDOWN: dict[str, float] = {}  # model -> unix timestamp allowed again

def _model_available(model: str) -> bool:
    ts = _LLM_COOLDOWN.get(model)
    return ts is None or ts <= time.time()

def _apply_cooldown(model: str, attempt: int):
    # Exponential: 10s, 30s, 90s, capped 300s
    base = 10
    delay = min(base * (3 ** (attempt-1)), 300)
    _LLM_COOLDOWN[model] = time.time() + delay


def openrouter_chat(system_prompt: str, user_prompt: str, image_base64: str | None = None):
    """Send chat (optionally multi‑modal) to OpenRouter with retry, fallback & cache.

    Strategy:
      1. Cache: Return cached answer if prompt (incl image flag + model) repeated.
      2. Try primary model (vision variant if image).
      3. On 429: exponential backoff (up to 3 attempts), then iterate fallback models.
      4. On non-429 HTTP errors: attempt next fallback immediately.
    """
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_KEY not configured on server")

    # Prepare model list (primary + fallbacks)
    # Round-robin primary model selection (text only). Vision requests stick to vision model.
    global _LLM_RR_INDEX
    if image_base64:
        primary = LLM_VISION_MODEL
    else:
        rr_list = [m.strip() for m in LLM_ROUND_ROBIN.split(',') if m.strip()] or [LLM_MODEL]
        primary = rr_list[_LLM_RR_INDEX % len(rr_list)]
        _LLM_RR_INDEX += 1
    fallbacks = [m.strip() for m in LLM_FALLBACK_MODEL.split(',') if m.strip()]
    model_chain = [primary] + [m for m in fallbacks if m != primary]
    if LLM_DISABLE_FALLBACKS:
        model_chain = [primary]

    # Cache key uses hash of combined inputs
    key_material = (
        primary
        + "|img="
        + ("1" if image_base64 else "0")
        + "|sys="
        + system_prompt
        + "|usr="
        + user_prompt
    )
    digest = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
    if digest in _LLM_CACHE:
        return _LLM_CACHE[digest]

    # Construct messages payload factory
    def build_messages(model_name: str):
        if image_base64 and model_name == primary:  # Only send image to first (vision) model
            return [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                        },
                    ],
                },
            ]
        else:
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    for model in model_chain:
        if not _model_available(model):
            continue  # skip cooling models
        backoff = 2.0
        for attempt in range(1, 4):  # up to 3 tries per model (mainly for 429)
            payload = {"model": model, "messages": build_messages(model)}
            try:
                if not _rate_limit_ok():
                    raise HTTPException(status_code=429, detail="Local rate limit exceeded; please wait a few seconds and retry.")
                resp = requests.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    json=payload,
                    timeout=90,
                    headers=headers,
                )
                if resp.status_code == 429:
                    last_error = f"429 from model {model} (attempt {attempt})"
                    _apply_cooldown(model, attempt)
                    # Adaptive strategy: after first 429 on this model, optionally reduce prompt length
                    if LLM_ADAPTIVE_RETRY and attempt == 1:
                        # Trim user text content to half if very long (>4k chars) and rebuild payload
                        # Locate user text in messages
                        for m in payload["messages"]:
                            if m.get("role") == "user":
                                if isinstance(m.get("content"), str) and len(m["content"]) > 4000:
                                    m["content"] = m["content"][:2000] + "\n\n[Truncated due to rate limit retry]"
                                elif isinstance(m.get("content"), list):
                                    for part in m["content"]:
                                        if part.get("type") == "text" and len(part.get("text","")) > 4000:
                                            part["text"] = part["text"][:2000] + "\n\n[Truncated due to rate limit retry]"
                    if attempt < 3:
                        # Jittered exponential backoff
                        jitter = 0.25 * backoff * (0.5 + (hash(f"{model}{attempt}{time.time()}") % 100) / 100.0)
                        time.sleep(backoff + jitter)
                        backoff *= 2
                        continue
                    else:
                        break  # move to next model
                if not resp.ok:
                    # Special handling: try normalized variants if invalid model ID (400)
                    if resp.status_code == 400 and "not a valid model ID" in resp.text.lower():
                        variants = []
                        # Remove trailing :free if present
                        if model.endswith(":free"):
                            variants.append(model.rsplit(":free", 1)[0])
                        # Add :latest variant
                        if not model.endswith(":latest"):
                            variants.append(model + ":latest")
                        # Short form without org prefix
                        if "/" in model:
                            short = model.split("/", 1)[1]
                            variants.append(short)
                        # Iterate variants immediately
                        for vm in variants:
                            payload_variant = {"model": vm, "messages": build_messages(vm)}
                            try:
                                vr = requests.post(
                                    f"{OPENROUTER_BASE}/chat/completions",
                                    json=payload_variant,
                                    timeout=60,
                                    headers=headers,
                                )
                                if vr.ok:
                                    data = vr.json()
                                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                                    _LLM_CACHE[digest] = content
                                    _LLM_CACHE_KEYS.append(digest)
                                    if len(_LLM_CACHE_KEYS) > LLM_CACHE_MAX:
                                        old_key = _LLM_CACHE_KEYS.pop(0)
                                        _LLM_CACHE.pop(old_key, None)
                                    return content
                            except requests.RequestException:
                                pass
                        last_error = f"Invalid model and variants failed for {model}: {resp.text[:160]}"
                        break  # go to next model
                    last_error = f"HTTP {resp.status_code} from model {model}: {resp.text[:200]}"
                    break  # don't retry non-429 for same model; go to next model
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                # Store in cache
                _LLM_CACHE[digest] = content
                _LLM_CACHE_KEYS.append(digest)
                if len(_LLM_CACHE_KEYS) > LLM_CACHE_MAX:
                    # FIFO trim
                    old_key = _LLM_CACHE_KEYS.pop(0)
                    _LLM_CACHE.pop(old_key, None)
                return content
            except HTTPException:
                raise
            except requests.RequestException as e:
                last_error = f"Request error model {model} attempt {attempt}: {e}"
                if attempt < 3:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    break  # Next model

    # Final degraded fallback: simple heuristic summary of user_prompt (no external call)
    # Try local HF model before heuristic if available/allowed
    local_answer = _local_generate(system_prompt, user_prompt)
    if local_answer:
        degraded_content = f"{local_answer}"
    else:
        degraded_content = _degraded_local_answer(user_prompt)
    # Cache degraded answer to avoid hammering
    _LLM_CACHE[digest] = degraded_content
    _LLM_CACHE_KEYS.append(digest)
    return degraded_content


def _degraded_local_answer(prompt: str) -> str:
    # Very naive extraction of bullet-style summary; ensures user still gets *something*.
    lines = [l.strip() for l in prompt.splitlines() if l.strip()]
    # Keep last 30 non-empty lines
    sample = lines[-30:]
    # Extract sentences with question marks or numbers
    focus = [l for l in sample if '?' in l or l[:2].isdigit()]
    if not focus:
        focus = sample
    summary = '\n'.join(focus[:10])
    return (
        "[DEGRADED MODE: All remote free models rate-limited. Returning heuristic summary.]\n\n"
        "Potential questions / key lines:\n" + summary + "\n\n"
        "Try again in ~30-60s for full AI solution."
    )

# ---------------- Local HF model fallback ----------------
_LOCAL_MODEL = None
_LOCAL_TOKENIZER = None
_LOCAL_FAILED = False

def _ensure_local_model():
    global _LOCAL_MODEL, _LOCAL_TOKENIZER, _LOCAL_FAILED
    if _LOCAL_FAILED:
        return False
    if _LOCAL_MODEL is not None and _LOCAL_TOKENIZER is not None:
        return True
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        _LOCAL_TOKENIZER = AutoTokenizer.from_pretrained(LLM_LOCAL_MODEL)
        _LOCAL_MODEL = AutoModelForCausalLM.from_pretrained(
            LLM_LOCAL_MODEL,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        return True
    except Exception:
        _LOCAL_FAILED = True
        return False

def _local_generate(system_prompt: str, user_prompt: str) -> str:
    if not _ensure_local_model():
        return ""
    import torch
    prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
    inputs = _LOCAL_TOKENIZER(prompt, return_tensors="pt")
    for k in inputs:
        inputs[k] = inputs[k].to(_LOCAL_MODEL.device)
    with torch.no_grad():
        out = _LOCAL_MODEL.generate(
            **inputs,
            max_new_tokens=LLM_LOCAL_MAX_NEW_TOKENS,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=_LOCAL_TOKENIZER.eos_token_id,
        )
    text = _LOCAL_TOKENIZER.decode(out[0], skip_special_tokens=True)
    # Extract assistant part after last user marker if present
    if "<|assistant|>" in text:
        text = text.split("<|assistant|>")[-1].strip()
    return text.strip()


@router.post("/ai/get-papers/{course_code}")
async def get_papers(course_code: str):
    """
    Download all PDFs for a course using Selenium (login required). If already downloaded, does nothing.
    If no PDFs exist for the course, exit early and return a message.
    """
    try:
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(PROJECT_ROOT, "ai/download_past_papers.py"),
                course_code,
                "download",
            ],
            capture_output=True,
            timeout=300,
        )
        # If download_past_papers.py returns False (no past papers), check stdout
        stdout = result.stdout.decode()
        if "No past papers found" in stdout:
            return {
                "message": f"No past papers found for {course_code}.",
                "output": stdout,
                "stderr": result.stderr.decode(),
                "no_papers": True,
            }
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.stderr.decode(),
                    "output": stdout,
                    "returncode": result.returncode,
                },
            )
        return {
            "message": "Download complete",
            "output": stdout,
            "stderr": result.stderr.decode(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/past-papers/{course_code}")
async def list_past_papers(course_code: str):
    """
    List all available past paper PDFs for a course from S3.
    """
    session = boto3.session.Session()
    s3 = session.client(
        service_name="s3",
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{course_code}/")
    pdfs = []
    for obj in response.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".pdf"):
            pdfs.append(os.path.basename(key))
    return pdfs


@router.get("/ai/past-papers/{course_code}/{filename}")
async def get_past_paper_pdf(course_code: str, filename: str):
    session = boto3.session.Session()
    s3 = session.client(
        service_name="s3",
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    s3_key = f"{course_code}/{filename}"
    try:
        s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return StreamingResponse(
            s3_obj["Body"],
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found in S3: {e}")


@router.post("/ai/generate-questions-json/{course_code}")
async def generate_questions_json(course_code: str):
    """
    Generate questions JSON for a given course code by running llama_exam_processor.py.
    Returns logs and file path.
    """
    try:
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(PROJECT_ROOT, "ai/llama_exam_processor.py"),
            ],
            capture_output=True,
            timeout=600,
            env={**os.environ, "COURSE_CODE": course_code},
        )
        stdout = proc.stdout.decode()
        stderr = proc.stderr.decode()
        filename = f"{course_code}_mock.json"
        json_path = os.path.join(PROJECT_ROOT, filename)
        if proc.returncode != 0:
            return {
                "success": False,
                "stdout": stdout,
                "stderr": stderr,
                "json_file": filename if os.path.exists(json_path) else None,
            }
        return {
            "success": True,
            "stdout": stdout,
            "stderr": stderr,
            "json_file": filename if os.path.exists(json_path) else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def upload_questions_to_supabase(json_path, quiz_id, table_name="questions"):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False, "Supabase credentials not set."
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    # Only keep specified columns, including options (as JSON if present)
    rows = []
    for q in questions:
        row = {
            "question_text": q.get("question_text", ""),
            "topic": q.get("topic", ""),
            "question_type": q.get("question_type", ""),
            "sample_answer": q.get("sample_answer", ""),
            "correct_answer": q.get("correct_answer", ""),
            "options": q.get("options", []) if q.get("options") is not None else [],
            "quiz_id": quiz_id,
        }
        rows.append(row)
    # Insert in batches of 50 using Supabase REST API
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    for i in range(0, len(rows), 50):
        batch = rows[i : i + 50]
        response = requests.post(url, headers=headers, data=json.dumps(batch))
        if not response.ok:
            return (
                False,
                f"Error uploading batch {i//50+1}: {response.status_code} {response.text}",
            )
    return True, f"Uploaded {len(rows)} questions to Supabase."


# Combined endpoint: create quiz and upload questions in one step
@router.post("/ai/create-quiz-and-upload-questions/{course_code}")
async def create_quiz_and_upload_questions(
    course_code: str,
    title: str,
    course_id: str,
    topic: str = "Mock Exam",
    description: str = "Generated by Mock Exam",
    time_limit: int = 60,
    user_id: str = None,
    ):
    """
    Create a new quiz and upload all questions from {COURSE_CODE}_mock.json to Supabase, linking them to the new quiz.
    """
    # 1. Create the quiz
    quiz_data = {
        "title": title,
        "description": description,
        "course_id": course_id,
        "topic": topic,
        "time_limit": time_limit,
    }
    if user_id:
        quiz_data["user_id"] = user_id
    async with httpx.AsyncClient() as client:
        quiz_resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/quiz",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json=quiz_data,
        )
        if quiz_resp.status_code not in [200, 201]:
            return {"success": False, "error": f"Quiz creation failed: {quiz_resp.text}"}
        quiz = quiz_resp.json()[0]
        quiz_id = quiz["id"]

    # 2. Upload questions with quiz_id
    filename = f"{course_code}_mock.json"
    json_path = os.path.join(PROJECT_ROOT, filename)
    if not os.path.exists(json_path):
        return {"success": False, "error": f"JSON file not found: {json_path}"}
    ok, msg = upload_questions_to_supabase(json_path, quiz_id=quiz_id)
    # Delete the local JSON file after upload
    if ok and os.path.exists(json_path):
        try:
            os.remove(json_path)
        except Exception as e:
            msg += f" (Warning: could not delete local file: {e})"
    return {"success": ok, "quiz": quiz, "message": msg}


# --- AI assistance for a page/viewport of a past paper ---
@router.post("/ai/solve-paper")
async def solve_paper(payload: dict):
    """Generate an AI solution / explanation for the supplied past paper viewport.

    Accepts JSON with:
      - text: (string) extracted text of current page/viewport (required if no image)
      - image_base64: (optional) PNG image (base64, no data URL header) of the page/viewport
      - course_code / filename / page_number: optional metadata
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    raw_text = (payload.get("text") or "").strip()
    image_b64 = payload.get("image_base64")
    if not raw_text and not image_b64:
        raise HTTPException(status_code=400, detail="Provide at least 'text' or 'image_base64'")

    max_chars = 12000
    truncated = raw_text[:max_chars]
    truncated_note = "" if len(raw_text) <= max_chars else "\n\n(Note: text truncated for length.)"

    # meta_bits = []
    # for key in ("course_code", "filename", "page_number"):
    #     if key in payload and payload[key] not in (None, ""):
    #         meta_bits.append(f"{key}={payload[key]}")
    # meta_line = ("Context: " + ", ".join(meta_bits)) if meta_bits else "Context: (not provided)"

    system_prompt = (
        "You are an academic assistant that provides concise, structured solutions to exam questions. "
        "Explain reasoning, show working for calculations, and if multiple distinct questions appear, number answers. "
        "If an image is provided, use it to infer any formulas, diagrams or figures referenced."
        "Do not ask for more information."
    )
    user_prompt = textwrap.dedent(
        f"""

        Provide solutions / guidance for the following exam page excerpt. If multiple questions or sub‑parts appear, address each separately.
        Text (may be truncated):\n{truncated if truncated else '(no text provided)'}

        Return:
        1. List of identified question numbers (if discernible). Do not provide the question text.
        2. Step-by-step reasoning / working
        3. Final answer(s). Multiple-choice questions must have only 1 answer.
        4. Key concepts involved
        {truncated_note}
        """
    ).strip()

    # Prefer OpenAI for fast, reliable chat if API key is present. If not, go straight to local.
    def llm_chat(system_prompt: str, user_prompt: str, image_b64: str | None = None):
        if OPENAI_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                payload = {
                    "model": OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 900,
                }
                resp = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            except requests.RequestException as e:
                print(f"OpenAI call failed: {e}")
        
        # No OpenAI key or OpenAI failed - try local model directly
        local_answer = _local_generate(system_prompt, user_prompt)
        if local_answer:
            return local_answer
        
        # Final degraded fallback if local also fails
        return _degraded_local_answer(user_prompt)

    # Call with correct keyword matching llm_chat parameter (image_b64)
    answer = llm_chat(system_prompt, user_prompt, image_b64=image_b64)
    return {"answer": answer}
