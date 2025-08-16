from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
import os
from typing import List

router = APIRouter()

PAST_PAPERS_DIR = os.path.join(os.getcwd(), "past_papers")

@router.post("/ai/extract-text/{course_code}")
async def extract_text_and_store(course_code: str):
    """
    Run the extractText.py script for a course, download and extract all PDFs, and store extracted text and PDFs.
    """
    import subprocess
    try:
        result = subprocess.run([
            "python3", "backend/ai/extractText.py", course_code
        ],
        capture_output=True,
        timeout=300
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.stderr.decode(),
                    "output": result.stdout.decode(),
                    "returncode": result.returncode
                }
            )
        return {"message": "Extraction complete", "output": result.stdout.decode(), "stderr": result.stderr.decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/past-papers/{course_code}")
async def list_past_papers(course_code: str):
    """
    List all available past paper PDFs for a course.
    """
    course_dir = os.path.join(PAST_PAPERS_DIR, course_code)
    if not os.path.exists(course_dir):
        return []
    pdfs = [f for f in os.listdir(course_dir) if f.endswith(".pdf")]
    return pdfs

@router.get("/ai/past-papers/{course_code}/{filename}")
async def get_past_paper_pdf(course_code: str, filename: str):
    """
    Download a specific past paper PDF for a course.
    """
    file_path = os.path.join(PAST_PAPERS_DIR, course_code, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

@router.get("/ai/past-papers/{course_code}/text/{txtfile}")
async def get_past_paper_text(course_code: str, txtfile: str):
    """
    Get extracted text for a specific past paper.
    """
    file_path = os.path.join(PAST_PAPERS_DIR, course_code, txtfile)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Text file not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return {"text": f.read()}
