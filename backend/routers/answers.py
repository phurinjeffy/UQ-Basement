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

router = APIRouter()

class Answer(BaseModel):
    question: str
    user_answer: str

@router.post("/add-answer")
async def add_answer(answer: Answer):
    """Add a user answer to Supabase"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_REST_URL}/answers",
                headers=get_supabase_headers(),
                json=answer.dict()
            )
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Supabase error: {resp.text}"
                )
            return {"message": "Answer saved", "data": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all/answers")
async def get_answers():
    """Get all answers from Supabase"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_REST_URL}/answers",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return {"answers": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
