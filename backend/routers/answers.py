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



class BulkAnswersRequest(BaseModel):
    user_id: str
    answers: list[dict]



@router.post("/add-answers")
async def add_answers_bulk(request: BulkAnswersRequest):
    """Add multiple answers for a user from a JSON payload"""
    try:
        user_id = request.user_id
        answers = request.answers
        # Prepare data for Supabase bulk insert
        supabase_answers = [
            {
                "question": a["question"],
                "user_answer": a["user_answer"],
                "user_id": user_id
            }
            for a in answers
        ]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_REST_URL}/answers",
                headers=get_supabase_headers(),
                json=supabase_answers
            )
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Supabase error: {resp.text}"
                )
            return {"message": "Answers saved", "data": resp.json()}
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
