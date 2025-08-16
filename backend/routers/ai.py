from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json
import sys
from fastapi import Query
import httpx

sys.stdout.reconfigure(encoding="utf-8")

import os
import subprocess
import sys
import boto3
from botocore.client import Config

router = APIRouter()
# Always use project root for past_papers dir
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# S3/Supabase config
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_BUCKET = "pdfs"  # Change to your bucket name if different


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


from fastapi.responses import StreamingResponse
import io


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


import requests


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
            return {
                "success": False,
                "error": f"Quiz creation failed: {quiz_resp.text}",
            }
        quiz = quiz_resp.json()[0]
        quiz_id = quiz["id"]

    # 2. Upload questions with quiz_id
    filename = f"{course_code}_mock.json"
    json_path = os.path.join(PROJECT_ROOT, filename)
    if not os.path.exists(json_path):
        return {"success": False, "error": f"JSON file not found: {json_path}"}
    ok, msg = upload_questions_to_supabase(json_path, quiz_id=quiz_id)
    return {"success": ok, "quiz": quiz, "message": msg}



@router.post("/ai/upload-questions-to-supabase/{course_code}")
async def upload_questions_to_supabase_endpoint(
    course_code: str,
    quiz_id: str = Query(..., description="Quiz UUID to assign to all questions"),
):
    """
    Convert {COURSE_CODE}_mock.json to rows and upload to Supabase 'questions' table with specified columns, setting quiz_id for all questions.
    """
    filename = f"{course_code}_mock.json"
    json_path = os.path.join(PROJECT_ROOT, filename)
    if not os.path.exists(json_path):
        return {"success": False, "error": f"JSON file not found: {json_path}"}
    ok, msg = upload_questions_to_supabase(json_path, quiz_id=quiz_id)
    return {"success": ok, "message": msg}
