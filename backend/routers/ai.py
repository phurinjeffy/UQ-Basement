from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import sys

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
S3_ENDPOINT_URL = "https://hwcaroqjyelhfiqvuskq.storage.supabase.co/storage/v1/s3"
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
                os.path.join(PROJECT_ROOT, "ai/extractText.py"),
                course_code,
                "download",
            ],
            capture_output=True,
            timeout=300,
        )
        # If extractText.py returns False (no past papers), check stdout
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
