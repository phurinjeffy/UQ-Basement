
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import os
import httpx
import json

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1"

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

router = APIRouter(prefix="/questions", tags=["questions"])


class Question(BaseModel):
    question_text: str
    topic: str
    question_type: str
    sample_answer: str



# POST /questions: Add a single question
@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_question(question: Question):
    """Add a single question to Supabase"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_REST_URL}/questions",
                headers=get_supabase_headers(),
                json=question.dict()
            )
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Supabase error: {resp.text}"
                )
            return {"message": "Question saved", "data": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# GET /questions: Get all questions
@router.get("/")
async def get_questions():
    """Get all questions from Supabase"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_REST_URL}/questions",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return {"questions": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
