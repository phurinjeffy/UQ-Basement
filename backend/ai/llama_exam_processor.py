import os
import json
import requests
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import boto3
from botocore.client import Config
from io import BytesIO

load_dotenv()


# --------------------------
# CONFIGURATION
# --------------------------
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_BUCKET = "pdfs"

COURSE_CODE = "DECO2500"
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL_NAME = "meta-llama/llama-3.2-3b-instruct:free"

if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_KEY environment variable not set.")


# --------------------------
# HELPERS
# --------------------------
def read_past_paper_files_from_s3(course_code):
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
    papers = []
    for obj in response.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".pdf"):
            s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            pdf_bytes = s3_obj["Body"].read()
            reader = PdfReader(BytesIO(pdf_bytes))
            text = ""
            for i, page in enumerate(reader.pages):
                if i == 0:  # skip first page
                    continue
                text += page.extract_text() + "\n"
            papers.append(text)
    return papers


def preprocess_exam_text(text):
    lines = text.splitlines()
    questions = []
    current_question = []
    for line in lines:
        if line.strip().startswith("Question") or line.strip().startswith("PART"):
            continue
        if (
            line.strip()
            and not line.strip().startswith("Semester")
            and not line.strip().startswith("Examination")
        ):
            current_question.append(line)
        if line.strip().endswith("?") or line.strip().endswith("."):
            if current_question:
                questions.append("\n".join(current_question))
                current_question = []
    return questions


def split_into_questions(text):
    questions = []
    lines = text.splitlines()
    current_question = []
    for line in lines:
        if line.strip().upper().startswith("QUESTION"):
            if current_question:
                questions.append("\n".join(current_question))
            current_question = [line]
        else:
            current_question.append(line)
    if current_question:
        questions.append("\n".join(current_question))
    return questions


def openrouter_chat(prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an academic assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    res = requests.post(
        f"{OPENROUTER_BASE}/chat/completions", json=payload, headers=headers
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]


# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    print("Reading past papers from S3...")
    papers = read_past_paper_files_from_s3(COURSE_CODE)

    if not papers:
        raise FileNotFoundError(f"No PDF files found in S3 for course {COURSE_CODE}")

    first_paper = papers[0]
    questions = preprocess_exam_text(first_paper)

    # Build prompt for only questions (no mock_exam)
    prompt = (
        "You are an academic assistant. For each original question, create an entry with:\n"
        '   - "question_text": the actual question being asked, excluding any options.\n'
        '   - "topic": main subject area of the question.\n'
        '   - "question_type": one of "multiple_choice", "short_answer", "essay", or "calculation".\n'
        '   - For "multiple_choice" questions, include an "options" field (array of strings, e.g., ["A) ...", "B) ...", ...]) and a "correct_answer" field (string, e.g., "A) ...").\n'
        '   - For "short_answer", "essay", or "calculation" questions, include a "sample_answer" field (string).\n'
        "\n"
        "IMPORTANT:\n"
        "- Do NOT include any duplicate keys in any object. Each object must have only one of each key.\n"
        "- Output ONLY valid JSON. Do NOT include any text, comments, or code block markers (such as ```json).\n"
        "- Use double quotes for all keys and string values.\n"
        "- Do NOT include trailing commas.\n"
        "- Do NOT include any explanations or text outside the JSON object.\n"
        "- If you cannot answer, output an empty JSON object: {}.\n"
        "\n"
        "JSON structure:\n"
        "{\n"
        '  "questions": [\n'
        '    {"question_text": "...", "topic": "...", "question_type": "multiple_choice", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "..."},\n'
        '    {"question_text": "...", "topic": "...", "question_type": "short_answer", "sample_answer": "..."},\n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Here are the original questions:\n"
    )
    for idx, q in enumerate(questions, 1):
        prompt += f"\n--- QUESTION {idx} START ---\n{q}\n--- QUESTION {idx} END ---\n"

    print(f"Sending API request for {len(questions)} questions...")
    response = openrouter_chat(prompt)

    print("AI response:\n")
    print(response)

    # Try to parse JSON and auto-fix common schema issues
    import re

    def fix_question(q):
        qt = q.get("question_type")
        if qt == "multiple_choice":
            return {
                "question_text": q.get("question_text"),
                "topic": q.get("topic"),
                "question_type": "multiple_choice",
                "options": q.get("options", []),
                "correct_answer": q.get("correct_answer", ""),
            }
        elif qt in ("short_answer", "essay", "calculation"):
            return {
                "question_text": q.get("question_text"),
                "topic": q.get("topic"),
                "question_type": qt,
                "sample_answer": q.get("sample_answer", ""),
            }
        else:
            return None

    cleaned = response.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    json_str = match.group(0) if match else cleaned
    json_str = json_str.replace("'", '"')
    json_str = (
        json_str.replace("“", '"').replace("”", '"').replace("‘", '"').replace("’", '"')
    )
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # Remove trailing commas

    filename = f"{COURSE_CODE}_mock.json"

    try:
        result = json.loads(json_str)
        # Auto-fix questions array only
        if "questions" in result:
            fixed = []
            for q in result["questions"]:
                fq = fix_question(q)
                if fq and fq["question_text"]:
                    fixed.append(fq)
            result["questions"] = fixed
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print("Analysis + mock exam saved to:", filename)
    except Exception as e:
        print("Failed to parse JSON:", e)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"Raw AI response saved to: {filename}")
