from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

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

# Updated Course Models to match UQ Library API structure exactly
class CourseCreate(BaseModel):
    """Model for creating a new course - matches UQ Library API structure"""
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

# Enrollment Models (Many-to-Many relationship)
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

# API Response Models
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

# Legacy models for backward compatibility (if needed)
class CourseEnrollment(BaseModel):
    """Legacy model for course enrollment (backward compatibility)"""
    name: str = Field(..., min_length=1, max_length=20, description="Course code")
    course_title: str = Field(..., min_length=1, max_length=200, description="Full course title")
    semester: Optional[str] = Field(None, max_length=20, description="Semester")
    year: Optional[int] = Field(None, ge=2000, le=2030, description="Academic year")