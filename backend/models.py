from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# ===== USER MODELS =====
class UserCreate(BaseModel):
    email: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123",
            }
        }

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str
    courses: Optional[List[dict]] = []

# ===== COURSE MODELS =====
class CourseCreate(BaseModel):
    """Model for creating a new course - matches UQ Library API structure exactly"""
    name: str = Field(..., min_length=1, max_length=20, description="Course code (e.g., CYBR7003)")
    url: str = Field(..., description="UQ Library resource URL")
    type: str = Field(..., description="Resource type (e.g., learning_resource)")
    course_title: str = Field(..., min_length=1, max_length=200, description="Full course title")
    campus: str = Field(..., description="Campus location (e.g., St Lucia)")
    period: str = Field(..., description="Academic period (e.g., Semester 1 2026)")

class CourseUpdate(BaseModel):
    """Model for updating course details"""
    name: Optional[str] = Field(None, min_length=1, max_length=20, description="Course code")
    url: Optional[str] = Field(None, description="UQ Library resource URL")
    type: Optional[str] = Field(None, description="Resource type")
    course_title: Optional[str] = Field(None, min_length=1, max_length=200, description="Full course title")
    campus: Optional[str] = Field(None, description="Campus location")
    period: Optional[str] = Field(None, description="Academic period")

class CourseResponse(BaseModel):
    """Model for course response data"""
    id: UUID
    name: str
    url: str
    type: str
    course_title: str
    campus: str
    period: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# UQ Library specific model for batch operations
class UQCourse(BaseModel):
    """Model that exactly matches UQ Library API response structure"""
    name: str = Field(..., description="Course code from UQ API")
    url: str = Field(..., description="UQ Library resource URL")
    type: str = Field(..., description="Resource type from UQ API")
    course_title: str = Field(..., description="Course title from UQ API")
    campus: str = Field(..., description="Campus from UQ API")
    period: str = Field(..., description="Period from UQ API")

# ===== ENROLLMENT MODELS =====
class EnrollmentCreate(BaseModel):
    """Model for creating a new enrollment"""
    user_id: UUID = Field(..., description="ID of the user to enroll")
    course_id: UUID = Field(..., description="ID of the course")
    semester: Optional[str] = Field(None, max_length=20, description="Semester (e.g., Fall, Spring)")
    year: Optional[int] = Field(None, ge=2000, le=2030, description="Academic year")
    grade: Optional[str] = Field(None, max_length=5, description="Grade received (e.g., A, B, C)")
    exam_date: Optional[str] = Field(None, description="Date of the exam (YYYY-MM-DD)")
    exam_time: Optional[str] = Field(None, description="Time of the exam (HH:MM, no timezone)")

class EnrollmentUpdate(BaseModel):
    """Model for updating enrollment details"""
    semester: Optional[str] = Field(None, max_length=20, description="Semester")
    year: Optional[int] = Field(None, ge=2000, le=2030, description="Academic year")
    grade: Optional[str] = Field(None, max_length=5, description="Grade received")

class EnrollmentResponse(BaseModel):
    """Model for enrollment response data"""
    id: UUID
    user_id: UUID
    course_id: UUID
    semester: Optional[str] = None
    year: Optional[int] = None
    grade: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ===== QUESTION AND CHOICE MODELS =====
class ChoiceCreate(BaseModel):
    """Model for creating a choice option"""
    choice_text: str = Field(..., min_length=1, description="The choice text")
    choice_letter: Optional[str] = Field(None, max_length=5, description="Choice letter (A, B, C, D)")
    is_correct: bool = Field(default=False, description="Whether this choice is correct")

class ChoiceResponse(BaseModel):
    """Model for choice response data"""
    id: int
    question_id: int
    choice_text: str
    choice_letter: Optional[str] = None
    is_correct: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    """Model for creating a new question"""
    question_text: str = Field(..., min_length=1, description="The question text")
    topic: str = Field(..., max_length=100, description="Question topic/category")
    question_type: str = Field(
        ..., 
        pattern="^(multiple_choice|short_answer|calculation)$",
        description="Type of question"
    )
    sample_answer: Optional[str] = Field(None, description="Sample answer or explanation")
    correct_answer: Optional[str] = Field(None, description="Correct answer for multiple choice")
    quiz_id: Optional[UUID] = Field(None, description="Associated quiz ID")  # ADD THIS LINE
    choices: Optional[List[ChoiceCreate]] = Field([], description="List of choices for multiple choice questions")

class QuestionUpdate(BaseModel):
    """Model for updating question details"""
    question_text: Optional[str] = Field(None, min_length=1, description="The question text")
    topic: Optional[str] = Field(None, max_length=100, description="Question topic/category")
    question_type: Optional[str] = Field(
        None, 
        pattern="^(multiple_choice|short_answer|calculation)$",
        description="Type of question"
    )
    sample_answer: Optional[str] = Field(None, description="Sample answer or explanation")
    correct_answer: Optional[str] = Field(None, description="Correct answer for multiple choice")
    quiz_id: Optional[UUID] = Field(None, description="Associated quiz ID")  # ADD THIS LINE

class QuestionResponse(BaseModel):
    """Model for question response data"""
    id: int
    question_text: str
    topic: str
    question_type: str
    sample_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    quiz_id: Optional[UUID] = None  # ADD THIS LINE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    choices: Optional[List[ChoiceResponse]] = []
    
    class Config:
        from_attributes = True

class QuestionWithChoices(BaseModel):
    """Extended question model with choices included"""
    id: int
    question_text: str
    topic: str
    question_type: str
    sample_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    quiz_id: Optional[UUID] = None  # ADD THIS LINE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    choices: List[Dict[str, Any]] = []

# ===== BULK IMPORT MODELS =====
class BulkQuestionData(BaseModel):
    """Model for individual question data in bulk import"""
    question_text: str
    topic: str
    question_type: str
    sample_answer: Optional[str] = ""
    correct_answer: Optional[str] = None
    options: Optional[List[str]] = []  # For multiple choice questions

class BulkImportRequest(BaseModel):
    """Model for bulk importing questions from JSON"""
    questions: List[Dict[str, Any]] = Field([], description="List of question objects")
    mock_exam: List[Dict[str, Any]] = Field([], description="List of mock exam question objects")
    quiz_id: Optional[UUID] = Field(None, description="Optional quiz ID to assign to all imported questions")  # ADD THIS LINE

class BulkImportResponse(BaseModel):
    """Model for bulk import operation response"""
    message: str
    imported_count: int
    skipped_count: int = 0
    errors: List[str] = []
    data: List[Dict[str, Any]] = []

# ===== QUIZ/EXAM MODELS =====
class QuizCreate(BaseModel):
    """Model for creating a quiz/exam"""
    title: str = Field(..., min_length=1, max_length=200, description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    course_id: UUID = Field(..., description="Associated course ID - REQUIRED")
    topic: Optional[str] = Field(None, max_length=100, description="Quiz topic/category")
    time_limit: Optional[int] = Field(None, ge=1, description="Time limit in minutes")

class QuizResponse(BaseModel):
    """Model for quiz response data"""
    id: UUID  # Changed from int to UUID
    title: str
    description: Optional[str] = None
    course_id: UUID = Field(..., description="Associated course ID")
    topic: Optional[str] = None
    time_limit: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    questions: List[QuestionWithChoices] = []
    
    class Config:
        from_attributes = True

class QuizAttemptCreate(BaseModel):
    """Model for creating a quiz attempt"""
    quiz_id: UUID = Field(..., description="ID of the quiz being attempted")  # Changed from int to UUID
    user_id: UUID = Field(..., description="ID of the user taking the quiz")
    answers: Dict[int, str] = Field({}, description="Dictionary of question_id: answer")

class QuizAttemptResponse(BaseModel):
    """Model for quiz attempt response"""
    id: int
    quiz_id: UUID  # Changed from int to UUID
    user_id: UUID
    score: Optional[float] = None
    max_score: Optional[float] = None
    percentage: Optional[float] = None
    completed_at: Optional[datetime] = None
    time_taken: Optional[int] = None  # in seconds
    answers: Dict[int, str] = {}
    
    class Config:
        from_attributes = True

# ===== API RESPONSE MODELS =====
class SyncResponse(BaseModel):
    """Model for sync operation responses"""
    message: str
    synced_courses: List[dict]
    skipped_courses: List[dict]
    errors: List[str]
    total_processed: int

class BatchCreateResponse(BaseModel):
    """Model for batch create operation responses"""
    message: str
    synced_courses: List[dict]
    skipped_courses: List[dict]
    errors: List[str]
    total_processed: int

class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    """Model for paginated responses"""
    items: List[Dict[str, Any]]
    total: int
    page: int = 1
    size: int = 50
    pages: int

# ===== LEGACY MODELS (for backward compatibility) =====
class CourseEnrollment(BaseModel):
    """Legacy model for course enrollment (backward compatibility)"""
    name: str = Field(..., min_length=1, max_length=20, description="Course code")
    course_title: str = Field(..., min_length=1, max_length=200, description="Full course title")
    semester: Optional[str] = Field(None, max_length=20, description="Semester")
    year: Optional[int] = Field(None, ge=2000, le=2030, description="Academic year")

# ===== SEARCH AND FILTER MODELS =====
class QuestionSearchParams(BaseModel):
    """Model for question search parameters"""
    topic: Optional[str] = None
    question_type: Optional[str] = None
    search_text: Optional[str] = None
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Number of items per page")

class QuestionFilterParams(BaseModel):
    """Model for advanced question filtering"""
    topics: Optional[List[str]] = []
    question_types: Optional[List[str]] = []
    has_choices: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# ===== STATISTICS MODELS =====
class QuestionStats(BaseModel):
    """Model for question statistics"""
    total_questions: int
    by_topic: Dict[str, int]
    by_type: Dict[str, int]
    multiple_choice_count: int
    short_answer_count: int
    calculation_count: int

class UserQuizStats(BaseModel):
    """Model for user quiz statistics"""
    user_id: UUID
    total_quizzes_taken: int
    average_score: Optional[float] = None
    best_score: Optional[float] = None
    total_time_spent: int = 0  # in seconds
    quizzes_by_topic: Dict[str, int] = {}

class QuizWithCourse(BaseModel):
    """Extended quiz model with course details included"""
    id: UUID
    title: str
    description: Optional[str] = None
    course_id: UUID
    topic: Optional[str] = None
    time_limit: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    course: Optional[Dict[str, Any]] = None  # Course details
    questions: List[QuestionWithChoices] = []
    question_count: int = 0

class QuizUpdate(BaseModel):
    """Model for updating quiz details"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    course_id: Optional[UUID] = Field(None, description="Associated course ID")
    topic: Optional[str] = Field(None, max_length=100, description="Quiz topic/category")
    time_limit: Optional[int] = Field(None, ge=1, description="Time limit in minutes")