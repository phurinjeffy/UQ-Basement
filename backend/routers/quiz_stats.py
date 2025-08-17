from fastapi import APIRouter, HTTPException
import httpx
from config import get_supabase_headers, SUPABASE_REST_URL, logger

router = APIRouter()

@router.get("/available-for-user/{user_id}")
async def get_available_quizzes_for_user(user_id: str):
    """Get count of all available quizzes for courses the user is enrolled in"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user's enrolled courses
            enrollments_resp = await client.get(
                f"{SUPABASE_REST_URL}/enrollments?user_id=eq.{user_id}&select=course_id",
                headers=get_supabase_headers()
            )
            
            if enrollments_resp.status_code != 200:
                raise HTTPException(
                    status_code=enrollments_resp.status_code,
                    detail=f"Failed to get enrollments: {enrollments_resp.text}"
                )
            
            enrollments = enrollments_resp.json()
            course_ids = [enrollment["course_id"] for enrollment in enrollments]
            
            if not course_ids:
                return {"total_available": 0, "course_ids": []}
            
            # Get all quizzes for these courses
            course_filter = ",".join(course_ids)
            quizzes_resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?course_id=in.({course_filter})&select=id,course_id,title",
                headers=get_supabase_headers()
            )
            
            if quizzes_resp.status_code != 200:
                return {"total_available": 0, "course_ids": course_ids}
            
            quizzes = quizzes_resp.json()
            total_available = len(quizzes)
            
            return {
                "total_available": total_available,
                "course_ids": course_ids,
                "quizzes": quizzes
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available quizzes for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
