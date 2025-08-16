from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import os
import httpx
from uuid import UUID

# Import models from your models file
from models import (
    QuizCreate, QuizUpdate, QuizResponse, QuizWithCourse,
    QuestionWithChoices, APIResponse
)

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

# POST /quiz: Create a new quiz
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
async def create_quiz(quiz: QuizCreate):
    """Create a new quiz"""
    try:
        async with httpx.AsyncClient() as client:
            # Verify course exists
            course_resp = await client.get(
                f"{SUPABASE_REST_URL}/courses?id=eq.{quiz.course_id}",
                headers=get_supabase_headers()
            )
            
            if course_resp.status_code != 200 or not course_resp.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            # Create quiz data
            quiz_data = {
                "title": quiz.title,
                "description": quiz.description,
                "course_id": str(quiz.course_id),
                "topic": quiz.topic,
                "time_limit": quiz.time_limit,
                "user_id": str(quiz.user_id)
            }
            
            # Create the quiz
            resp = await client.post(
                f"{SUPABASE_REST_URL}/quiz",
                headers=get_supabase_headers(),
                json=quiz_data
            )
            
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Supabase error: {resp.text}"
                )
            
            created_quiz = resp.json()[0]
            
            return APIResponse(
                success=True,
                message="Quiz created successfully",
                data=created_quiz
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /quiz: Get all quizzes with optional filtering
@router.get("/", response_model=List[QuizResponse])
async def get_quizzes(
    course_id: Optional[UUID] = Query(None, description="Filter by course ID"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    include_questions: bool = Query(False, description="Include questions in response")
):
    """Get all quizzes with optional filtering"""
    try:
        async with httpx.AsyncClient() as client:
            # Build query parameters
            query_params = []
            
            if course_id:
                query_params.append(f"course_id=eq.{course_id}")
            if topic:
                query_params.append(f"topic=eq.{topic}")
            
            # Add pagination
            offset = (page - 1) * size
            query_params.extend([f"limit={size}", f"offset={offset}"])
            
            query_string = "&".join(query_params) if query_params else f"limit={size}&offset={offset}"
            quizzes_url = f"{SUPABASE_REST_URL}/quiz?{query_string}"
            
            # Get quizzes
            quizzes_resp = await client.get(quizzes_url, headers=get_supabase_headers())
            
            if quizzes_resp.status_code != 200:
                raise HTTPException(status_code=quizzes_resp.status_code, detail=quizzes_resp.text)
            
            quizzes = quizzes_resp.json()
            
            # If include_questions is True, fetch questions for each quiz
            if include_questions:
                for quiz in quizzes:
                    # Get questions for this quiz
                    questions_resp = await client.get(
                        f"{SUPABASE_REST_URL}/questions?quiz_id=eq.{quiz['id']}&select=*",
                        headers=get_supabase_headers()
                    )
                    
                    questions = questions_resp.json() if questions_resp.status_code == 200 else []
                    
                    # Get choices for each question
                    for question in questions:
                        choices_resp = await client.get(
                            f"{SUPABASE_REST_URL}/choices?question_id=eq.{question['id']}",
                            headers=get_supabase_headers()
                        )
                        choices = choices_resp.json() if choices_resp.status_code == 200 else []
                        question["choices"] = choices
                    
                    quiz["questions"] = questions
            else:
                # Just add empty questions list for consistency
                for quiz in quizzes:
                    quiz["questions"] = []
            
            return quizzes
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/by-user/{user_id}", response_model=APIResponse)
async def get_quizzes_by_user(user_id: str):
    """Get all quizzes created by a specific user."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?user_id=eq.{user_id}",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            quizzes = resp.json()
            return APIResponse(success=True, message="Quizzes fetched successfully", data={"quizzes": quizzes})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /quiz/{quiz_id}: Get a single quiz with questions and choices
@router.get("/{quiz_id}", response_model=QuizWithCourse)
async def get_quiz(quiz_id: UUID, include_course: bool = Query(True, description="Include course details")):
    """Get a single quiz with its questions and choices"""
    try:
        async with httpx.AsyncClient() as client:
            # Get the quiz
            quiz_resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?id=eq.{quiz_id}",
                headers=get_supabase_headers()
            )
            
            if quiz_resp.status_code != 200:
                raise HTTPException(status_code=quiz_resp.status_code, detail=quiz_resp.text)
            
            quizzes = quiz_resp.json()
            if not quizzes:
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            quiz = quizzes[0]
            
            # Get course details if requested
            if include_course:
                course_resp = await client.get(
                    f"{SUPABASE_REST_URL}/courses?id=eq.{quiz['course_id']}",
                    headers=get_supabase_headers()
                )
                if course_resp.status_code == 200 and course_resp.json():
                    quiz["course"] = course_resp.json()[0]
            
            # Get questions for this quiz
            questions_resp = await client.get(
                f"{SUPABASE_REST_URL}/questions?quiz_id=eq.{quiz_id}",
                headers=get_supabase_headers()
            )
            
            questions = questions_resp.json() if questions_resp.status_code == 200 else []
            
            # Get choices for each question
            for question in questions:
                choices_resp = await client.get(
                    f"{SUPABASE_REST_URL}/choices?question_id=eq.{question['id']}",
                    headers=get_supabase_headers()
                )
                choices = choices_resp.json() if choices_resp.status_code == 200 else []
                question["choices"] = choices
            
            quiz["questions"] = questions
            quiz["question_count"] = len(questions)
            
            return quiz
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PUT /quiz/{quiz_id}: Update a quiz
@router.put("/{quiz_id}", response_model=APIResponse)
async def update_quiz(quiz_id: UUID, quiz_update: QuizUpdate):
    """Update a quiz"""
    try:
        async with httpx.AsyncClient() as client:
            # Build update data (only include non-None fields)
            update_data = {k: v for k, v in quiz_update.dict().items() if v is not None}
            
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # If updating course_id, verify the course exists
            if 'course_id' in update_data:
                course_resp = await client.get(
                    f"{SUPABASE_REST_URL}/courses?id=eq.{update_data['course_id']}",
                    headers=get_supabase_headers()
                )
                if course_resp.status_code != 200 or not course_resp.json():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Course not found"
                    )
                update_data['course_id'] = str(update_data['course_id'])
            
            resp = await client.patch(
                f"{SUPABASE_REST_URL}/quiz?id=eq.{quiz_id}",
                headers=get_supabase_headers(),
                json=update_data
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            updated_quizzes = resp.json()
            if not updated_quizzes:
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            return APIResponse(
                success=True,
                message="Quiz updated successfully",
                data=updated_quizzes[0]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DELETE /quiz/{quiz_id}: Delete a quiz and its questions
@router.delete("/{quiz_id}", response_model=APIResponse)
async def delete_quiz(quiz_id: UUID, force: bool = Query(False, description="Force delete even if questions exist")):
    """Delete a quiz and all its questions"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if quiz exists
            quiz_resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?id=eq.{quiz_id}",
                headers=get_supabase_headers()
            )
            
            if quiz_resp.status_code != 200 or not quiz_resp.json():
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            quiz = quiz_resp.json()[0]
            
            # Check for existing questions
            if not force:
                questions_resp = await client.get(
                    f"{SUPABASE_REST_URL}/questions?quiz_id=eq.{quiz_id}&select=id",
                    headers=get_supabase_headers()
                )
                
                if questions_resp.status_code == 200:
                    questions = questions_resp.json()
                    if questions:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cannot delete quiz with {len(questions)} questions. Use force=true to override."
                        )
            
            # Delete the quiz (questions will be deleted automatically due to CASCADE)
            delete_resp = await client.delete(
                f"{SUPABASE_REST_URL}/quiz?id=eq.{quiz_id}",
                headers=get_supabase_headers()
            )
            
            if delete_resp.status_code != 200:
                raise HTTPException(status_code=delete_resp.status_code, detail=delete_resp.text)
            
            return APIResponse(
                success=True,
                message="Quiz deleted successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /quiz/{quiz_id}/questions: Get all questions for a specific quiz
@router.get("/{quiz_id}/questions", response_model=List[QuestionWithChoices])
async def get_quiz_questions(quiz_id: UUID):
    """Get all questions for a specific quiz"""
    try:
        async with httpx.AsyncClient() as client:
            # Verify quiz exists
            quiz_resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?id=eq.{quiz_id}&select=id",
                headers=get_supabase_headers()
            )
            
            if quiz_resp.status_code != 200 or not quiz_resp.json():
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            # Get questions for this quiz
            questions_resp = await client.get(
                f"{SUPABASE_REST_URL}/questions?quiz_id=eq.{quiz_id}",
                headers=get_supabase_headers()
            )
            
            if questions_resp.status_code != 200:
                raise HTTPException(status_code=questions_resp.status_code, detail=questions_resp.text)
            
            questions = questions_resp.json()
            
            # Get choices for each question
            for question in questions:
                choices_resp = await client.get(
                    f"{SUPABASE_REST_URL}/choices?question_id=eq.{question['id']}",
                    headers=get_supabase_headers()
                )
                choices = choices_resp.json() if choices_resp.status_code == 200 else []
                question["choices"] = choices
            
            return questions
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST /quiz/{quiz_id}/questions/{question_id}: Assign existing question to quiz
@router.post("/{quiz_id}/questions/{question_id}", response_model=APIResponse)
async def assign_question_to_quiz(quiz_id: UUID, question_id: UUID):
    """Assign an existing question to a quiz"""
    try:
        async with httpx.AsyncClient() as client:
            # Verify quiz exists
            quiz_resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?id=eq.{quiz_id}&select=id",
                headers=get_supabase_headers()
            )
            
            if quiz_resp.status_code != 200 or not quiz_resp.json():
                raise HTTPException(status_code=404, detail="Quiz not found")
            
            # Update question to assign it to the quiz
            resp = await client.patch(
                f"{SUPABASE_REST_URL}/questions?id=eq.{question_id}",
                headers=get_supabase_headers(),
                json={"quiz_id": str(quiz_id)}
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            updated_questions = resp.json()
            if not updated_questions:
                raise HTTPException(status_code=404, detail="Question not found")
            
            return APIResponse(
                success=True,
                message="Question assigned to quiz successfully",
                data=updated_questions[0]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DELETE /quiz/{quiz_id}/questions/{question_id}: Remove question from quiz
@router.delete("/{quiz_id}/questions/{question_id}", response_model=APIResponse)
async def remove_question_from_quiz(quiz_id: UUID, question_id: UUID):
    """Remove a question from a quiz (sets quiz_id to null)"""
    try:
        async with httpx.AsyncClient() as client:
            # Update question to remove it from the quiz
            resp = await client.patch(
                f"{SUPABASE_REST_URL}/questions?id=eq.{question_id}&quiz_id=eq.{quiz_id}",
                headers=get_supabase_headers(),
                json={"quiz_id": None}
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            
            updated_questions = resp.json()
            if not updated_questions:
                raise HTTPException(status_code=404, detail="Question not found in this quiz")
            
            return APIResponse(
                success=True,
                message="Question removed from quiz successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /quiz/course/{course_id}: Get all quizzes for a specific course
@router.get("/course/{course_id}", response_model=List[QuizResponse])
async def get_quizzes_by_course(course_id: UUID, include_questions: bool = Query(False, description="Include questions")):
    """Get all quizzes for a specific course"""
    try:
        async with httpx.AsyncClient() as client:
            # Verify course exists
            course_resp = await client.get(
                f"{SUPABASE_REST_URL}/courses?id=eq.{course_id}&select=id",
                headers=get_supabase_headers()
            )
            
            if course_resp.status_code != 200 or not course_resp.json():
                raise HTTPException(status_code=404, detail="Course not found")
            
            # Get quizzes for this course
            quizzes_resp = await client.get(
                f"{SUPABASE_REST_URL}/quiz?course_id=eq.{course_id}",
                headers=get_supabase_headers()
            )
            
            if quizzes_resp.status_code != 200:
                raise HTTPException(status_code=quizzes_resp.status_code, detail=quizzes_resp.text)
            
            quizzes = quizzes_resp.json()
            
            # Optionally include questions
            if include_questions:
                for quiz in quizzes:
                    questions_resp = await client.get(
                        f"{SUPABASE_REST_URL}/questions?quiz_id=eq.{quiz['id']}",
                        headers=get_supabase_headers()
                    )
                    questions = questions_resp.json() if questions_resp.status_code == 200 else []
                    
                    # Get choices for each question
                    for question in questions:
                        choices_resp = await client.get(
                            f"{SUPABASE_REST_URL}/choices?question_id=eq.{question['id']}",
                            headers=get_supabase_headers()
                        )
                        choices = choices_resp.json() if choices_resp.status_code == 200 else []
                        question["choices"] = choices
                    
                    quiz["questions"] = questions
            else:
                for quiz in quizzes:
                    quiz["questions"] = []
            
            return quizzes
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))