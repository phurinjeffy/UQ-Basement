from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import subprocess

router = APIRouter()
# Always use project root for past_papers dir
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAST_PAPERS_DIR = os.path.join(PROJECT_ROOT, "past_papers")


@router.post("/ai/get-papers/{course_code}")
async def get_papers(course_code: str):
    """
    Download all PDFs for a course using Selenium (login required). If already downloaded, does nothing.
    """
    try:
        result = subprocess.run(
            ["python3", "backend/ai/extractText.py", course_code, "download"],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.stderr.decode(),
                    "output": result.stdout.decode(),
                    "returncode": result.returncode,
                },
            )
        return {
            "message": "Download complete",
            "output": result.stdout.decode(),
            "stderr": result.stderr.decode(),
        }
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
    file_path = os.path.join(PAST_PAPERS_DIR, course_code, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
