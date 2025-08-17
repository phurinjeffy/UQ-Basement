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
        "Prefer": "return=representation",
    }


router = APIRouter()


class BulkAnswersRequest(BaseModel):
    user_id: str
    quiz_id: str
    answers: list[dict]


@router.post("/add-answers")
async def add_answers_bulk(request: BulkAnswersRequest):
    """Add multiple answers for a user and quiz from a JSON payload"""
    try:
        user_id = request.user_id
        quiz_id = request.quiz_id
        answers = request.answers
        # Prepare data for Supabase bulk insert
        supabase_answers = [
            {
                "question": a["question"],
                "user_answer": a["user_answer"],
                "user_id": user_id,
                "quiz_id": quiz_id,
            }
            for a in answers
        ]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SUPABASE_REST_URL}/answers",
                headers=get_supabase_headers(),
                json=supabase_answers,
            )
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=resp.status_code, detail=f"Supabase error: {resp.text}"
                )
            return {"message": "Answers saved", "data": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import Query


@router.get("/all/answers")
async def get_answers(user_id: str = Query(None), quiz_id: str = Query(None)):
    """Get all answers from Supabase, optionally filtered by user_id and quiz_id"""
    try:
        # Build query string for Supabase
        query_params = []
        if user_id:
            query_params.append(f"user_id=eq.{user_id}")
        if quiz_id:
            query_params.append(f"quiz_id=eq.{quiz_id}")
        query_string = "&".join(query_params)
        url = f"{SUPABASE_REST_URL}/answers"
        if query_string:
            url += f"?{query_string}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=get_supabase_headers())
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return {"answers": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/checks/{user_id}/{quiz_id}")
async def get_checks_by_user_and_quiz(user_id: str, quiz_id: str):
    """Get an array of checks for a user and quiz."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_REST_URL}/checked_answers?user_id=eq.{user_id}&quiz_id=eq.{quiz_id}",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            checked_answers = resp.json()
            all_checks = []
            
            for row in checked_answers:
                # Extract the check JSON from each row
                check_data = row.get("checks")
                
                # If check_data is a string (JSON), parse it
                if isinstance(check_data, str):
                    try:
                        check_data = json.loads(check_data)
                    except json.JSONDecodeError:
                        continue
                
                # If check_data is valid, add it to all_checks
                if check_data:
                    all_checks.append(check_data)
            
            return {"checks": all_checks}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-exam-stats/{user_id}")
async def get_user_exam_stats(user_id: str):
    """Get statistics about exams taken by a user (based on submitted answers)"""
    try:
        async with httpx.AsyncClient() as client:
            # Get distinct quiz_ids from answers table for this user
            resp = await client.get(
                f"{SUPABASE_REST_URL}/answers?user_id=eq.{user_id}&select=quiz_id",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            answers = resp.json()
            
            # Get unique quiz_ids (exams taken)
            unique_quiz_ids = list(set(answer["quiz_id"] for answer in answers if answer.get("quiz_id")))
            exams_taken = len(unique_quiz_ids)
            
            # Get checked answers to calculate average score
            checked_resp = await client.get(
                f"{SUPABASE_REST_URL}/checked_answers?user_id=eq.{user_id}&select=checks",
                headers=get_supabase_headers()
            )
            
            avg_score = 0
            if checked_resp.status_code == 200:
                checked_answers = checked_resp.json()
                total_score = 0
                total_exams_with_scores = 0
                
                for row in checked_answers:
                    check_data = row.get("checks")
                    if isinstance(check_data, str):
                        try:
                            check_data = json.loads(check_data)
                        except json.JSONDecodeError:
                            continue
                    
                    if check_data and isinstance(check_data, dict):
                        # Calculate score from check_data
                        correct = 0
                        total = 0
                        for key, value in check_data.items():
                            if isinstance(value, dict) and "correct" in value:
                                total += 1
                                if value["correct"]:
                                    correct += 1
                        
                        if total > 0:
                            score = (correct / total) * 100
                            total_score += score
                            total_exams_with_scores += 1
                
                if total_exams_with_scores > 0:
                    avg_score = round(total_score / total_exams_with_scores, 1)
            
            return {
                "exams_taken": exams_taken,
                "avg_score": avg_score,
                "unique_quiz_ids": unique_quiz_ids
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))