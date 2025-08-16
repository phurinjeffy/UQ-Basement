from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import os
import httpx
import json
from uuid import UUID

# Import models from your models file
from models import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionWithChoices,
    ChoiceCreate, ChoiceResponse,
    BulkImportRequest, BulkImportResponse,
    QuestionSearchParams, QuestionStats,
    APIResponse
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

router = APIRouter(prefix="/questions", tags=["questions"])

# Helper function to parse multiple choice options
def parse_choices(options: List[str], correct_answer: str = None) -> List[ChoiceCreate]:
    choices = []
    for option in options:
        # Extract letter (A, B, C, D) from option text like "A) Some text"
        choice_letter = option.split(")")[0].strip() if ")" in option else None
        choice_text = option.split(")", 1)[1].strip() if ")" in option else option
        
        # Check if this is the correct answer
        is_correct = correct_answer and option == correct_answer
        
        choices.append(ChoiceCreate(
            choice_text=choice_text,
            choice_letter=choice_letter,
            is_correct=is_correct
        ))
    
    return choices

# POST /questions: Add a single question
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
async def add_question(question: QuestionCreate):
    """Add a single question with choices to Supabase"""
    try:
        async with httpx.AsyncClient() as client:
            # First, create the question
            question_data = {
                "question_text": question.question_text,
                "topic": question.topic,
                "question_type": question.question_type,
                "sample_answer": question.sample_answer,
                "correct_answer": question.correct_answer,
                "quiz_id": question.quiz_id  # ADD THIS LINE
            }
            
            resp = await client.post(
                f"{SUPABASE_REST_URL}/questions",
                headers=get_supabase_headers(),
                json=question_data
            )
            
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Supabase error: {resp.text}"
                )
            
            created_question = resp.json()[0]
            question_id = created_question["id"]
            
            # If there are choices, add them
            if question.choices:
                choices_data = []
                for choice in question.choices:
                    choices_data.append({
                        "question_id": question_id,
                        "choice_text": choice.choice_text,
                        "choice_letter": choice.choice_letter,
                        "is_correct": choice.is_correct
                    })
                
                # Insert all choices
                choices_resp = await client.post(
                    f"{SUPABASE_REST_URL}/choices",
                    headers=get_supabase_headers(),
                    json=choices_data
                )
                
                if choices_resp.status_code not in [200, 201]:
                    # If choices fail, we might want to delete the question or log the error
                    print(f"Warning: Failed to add choices for question {question_id}")
            
            return APIResponse(
                success=True,
                message="Question saved successfully",
                data=created_question
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST /questions/bulk-import: Import questions from JSON
@router.post("/bulk-import", status_code=status.HTTP_201_CREATED, response_model=BulkImportResponse)
async def bulk_import_questions(import_data: BulkImportRequest):
    """Import questions from JSON file structure"""
    try:
        all_questions = []
        
        # Process regular questions
        if import_data.questions:
            all_questions.extend(import_data.questions)
        
        # Process mock exam questions
        if import_data.mock_exam:
            all_questions.extend(import_data.mock_exam)
        
        created_questions = []
        errors = []
        skipped_count = 0
        
        async with httpx.AsyncClient() as client:
            for q_data in all_questions:
                # Skip questions with empty question_text
                if not q_data.get("question_text", "").strip():
                    skipped_count += 1
                    continue
                
                try:
                    # Prepare question data
                    question_data = {
                        "question_text": q_data.get("question_text", ""),
                        "topic": q_data.get("topic", ""),
                        "question_type": q_data.get("question_type", "short_answer"),
                        "sample_answer": q_data.get("sample_answer", ""),
                        "correct_answer": q_data.get("correct_answer", ""),
                        "quiz_id": q_data.get("quiz_id")
                    }
                    
                    # Create question
                    resp = await client.post(
                        f"{SUPABASE_REST_URL}/questions",
                        headers=get_supabase_headers(),
                        json=question_data
                    )
                    
                    if resp.status_code not in [200, 201]:
                        errors.append(f"Failed to create question: {resp.text}")
                        continue
                    
                    created_question = resp.json()[0]
                    question_id = created_question["id"]
                    
                    # Handle multiple choice options
                    if q_data.get("question_type") == "multiple_choice" and q_data.get("options"):
                        choices = parse_choices(
                            q_data["options"], 
                            q_data.get("correct_answer")
                        )
                        
                        choices_data = []
                        for choice in choices:
                            choices_data.append({
                                "question_id": question_id,
                                "choice_text": choice.choice_text,
                                "choice_letter": choice.choice_letter,
                                "is_correct": choice.is_correct
                            })
                        
                        # Insert choices
                        if choices_data:
                            choices_resp = await client.post(
                                f"{SUPABASE_REST_URL}/choices",
                                headers=get_supabase_headers(),
                                json=choices_data
                            )
                            
                            if choices_resp.status_code not in [200, 201]:
                                errors.append(f"Failed to create choices for question {question_id}")
                    
                    created_questions.append(created_question)
                    
                except Exception as e:
                    errors.append(f"Error processing question: {str(e)}")
                    skipped_count += 1
        
        return BulkImportResponse(
            message=f"Successfully imported {len(created_questions)} questions",
            imported_count=len(created_questions),
            skipped_count=skipped_count,
            errors=errors,
            data=created_questions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /questions: Get all questions with choices and search/filter support
@router.get("/", response_model=List[QuestionWithChoices])
async def get_questions(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    search: Optional[str] = Query(None, description="Search in question text"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size")
):
    """Get all questions with their choices from Supabase with optional filtering"""
    try:
        async with httpx.AsyncClient() as client:
            # Build query parameters
            query_params = []
            
            if topic:
                query_params.append(f"topic=eq.{topic}")
            if question_type:
                query_params.append(f"question_type=eq.{question_type}")
            if search:
                query_params.append(f"question_text=ilike.*{search}*")
            
            # Add pagination
            offset = (page - 1) * size
            query_params.extend([f"limit={size}", f"offset={offset}"])
            
            query_string = "&".join(query_params) if query_params else ""
            questions_url = f"{SUPABASE_REST_URL}/questions"
            if query_string:
                questions_url += f"?{query_string}"
            
            # Get filtered questions
            questions_resp = await client.get(questions_url, headers=get_supabase_headers())
            
            if questions_resp.status_code != 200:
                raise HTTPException(status_code=questions_resp.status_code, detail=questions_resp.text)
            
            questions = questions_resp.json()
            
            # Get all choices
            choices_resp = await client.get(
                f"{SUPABASE_REST_URL}/choices",
                headers=get_supabase_headers()
            )
            
            choices = choices_resp.json() if choices_resp.status_code == 200 else []
            
            # Group choices by question_id
            choices_by_question = {}
            for choice in choices:
                question_id = choice["question_id"]
                if question_id not in choices_by_question:
                    choices_by_question[question_id] = []
                choices_by_question[question_id].append(choice)
            
            # Attach choices to questions
            for question in questions:
                question["choices"] = choices_by_question.get(question["id"], [])
            
            return questions
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{question_id}", response_model=QuestionWithChoices)
async def get_question(question_id: UUID):
    """Get a single question with its choices"""
    try:
        async with httpx.AsyncClient() as client:
            # Get the question
            question_resp = await client.get(
                f"{SUPABASE_REST_URL}/questions?id=eq.{question_id}",
                headers=get_supabase_headers()
            )
            if question_resp.status_code != 200:
                raise HTTPException(status_code=question_resp.status_code, detail=question_resp.text)
            questions = question_resp.json()
            if not questions:
                raise HTTPException(status_code=404, detail="Question not found")
            question = questions[0]
            # Get choices for this question
            choices_resp = await client.get(
                f"{SUPABASE_REST_URL}/choices?question_id=eq.{question_id}",
                headers=get_supabase_headers()
            )
            choices = choices_resp.json() if choices_resp.status_code == 200 else []
            question["choices"] = choices
            return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{question_id}", response_model=APIResponse)
async def update_question(question_id: UUID, question_update: QuestionUpdate):
    """Update a question"""
    try:
        async with httpx.AsyncClient() as client:
            update_data = {k: v for k, v in question_update.dict().items() if v is not None}
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            resp = await client.patch(
                f"{SUPABASE_REST_URL}/questions?id=eq.{question_id}",
                headers=get_supabase_headers(),
                json=update_data
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            updated_questions = resp.json()
            if not updated_questions:
                raise HTTPException(status_code=404, detail="Question not found")
            return APIResponse(
                success=True,
                message="Question updated successfully",
                data=updated_questions[0]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{question_id}", response_model=APIResponse)
async def delete_question(question_id: UUID):
    """Delete a question and all its choices"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{SUPABASE_REST_URL}/questions?id=eq.{question_id}",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            deleted_questions = resp.json()
            if not deleted_questions:
                raise HTTPException(status_code=404, detail="Question not found")
            return APIResponse(
                success=True,
                message="Question deleted successfully"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /questions/stats: Get question statistics
@router.get("/stats", response_model=QuestionStats)
async def get_question_stats():
    """Get statistics about questions"""
    try:
        async with httpx.AsyncClient() as client:
            # Get all questions
            questions_resp = await client.get(
                f"{SUPABASE_REST_URL}/questions?select=topic,question_type",
                headers=get_supabase_headers()
            )
            
            if questions_resp.status_code != 200:
                raise HTTPException(status_code=questions_resp.status_code, detail=questions_resp.text)
            
            questions = questions_resp.json()
            
            # Calculate statistics
            total_questions = len(questions)
            by_topic = {}
            by_type = {}
            
            for question in questions:
                topic = question.get("topic", "Unknown")
                question_type = question.get("question_type", "unknown")
                
                by_topic[topic] = by_topic.get(topic, 0) + 1
                by_type[question_type] = by_type.get(question_type, 0) + 1
            
            return QuestionStats(
                total_questions=total_questions,
                by_topic=by_topic,
                by_type=by_type,
                multiple_choice_count=by_type.get("multiple_choice", 0),
                short_answer_count=by_type.get("short_answer", 0),
                calculation_count=by_type.get("calculation", 0)
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /questions/topics: Get all unique topics
@router.get("/topics", response_model=List[str])
async def get_topics():
    """Get all unique topics from questions"""
    try:
        async with httpx.AsyncClient() as client:
            questions_resp = await client.get(
                f"{SUPABASE_REST_URL}/questions?select=topic",
                headers=get_supabase_headers()
            )
            
            if questions_resp.status_code != 200:
                raise HTTPException(status_code=questions_resp.status_code, detail=questions_resp.text)
            
            questions = questions_resp.json()
            topics = list(set(q.get("topic", "") for q in questions if q.get("topic", "").strip()))
            return sorted(topics)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{question_id}/choices", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
async def add_choices_to_question(question_id: UUID, choices: List[ChoiceCreate]):
    """Add choices to an existing question"""
    try:
        async with httpx.AsyncClient() as client:
            question_resp = await client.get(
                f"{SUPABASE_REST_URL}/questions?id=eq.{question_id}",
                headers=get_supabase_headers()
            )
            if question_resp.status_code != 200:
                raise HTTPException(status_code=question_resp.status_code, detail=question_resp.text)
            questions = question_resp.json()
            if not questions:
                raise HTTPException(status_code=404, detail="Question not found")
            choices_data = []
            for choice in choices:
                choices_data.append({
                    "question_id": str(question_id),
                    "choice_text": choice.choice_text,
                    "choice_letter": choice.choice_letter,
                    "is_correct": choice.is_correct
                })
            choices_resp = await client.post(
                f"{SUPABASE_REST_URL}/choices",
                headers=get_supabase_headers(),
                json=choices_data
            )
            if choices_resp.status_code not in [200, 201]:
                raise HTTPException(status_code=choices_resp.status_code, detail=choices_resp.text)
            created_choices = choices_resp.json()
            return APIResponse(
                success=True,
                message=f"Successfully added {len(created_choices)} choices to question",
                data=created_choices
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{question_id}/choices/{choice_id}", response_model=APIResponse)
async def delete_choice(question_id: UUID, choice_id: UUID):
    """Delete a specific choice from a question"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{SUPABASE_REST_URL}/choices?id=eq.{choice_id}&question_id=eq.{question_id}",
                headers=get_supabase_headers()
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            deleted_choices = resp.json()
            if not deleted_choices:
                raise HTTPException(status_code=404, detail="Choice not found")
            return APIResponse(
                success=True,
                message="Choice deleted successfully"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))