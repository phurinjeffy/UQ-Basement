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

class CourseCreate(BaseModel):
    """Model for creating a new course"""
    course_code: str = Field(..., min_length=1, max_length=20, description="Course code (e.g., CS101)")
    course_name: str = Field(..., min_length=1, max_length=200, description="Full course name")
    description: Optional[str] = Field(None, max_length=1000, description="Course description")
    credits: Optional[int] = Field(None, ge=1, le=10, description="Credit hours")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    instructor: Optional[str] = Field(None, max_length=100, description="Instructor name")

class CourseUpdate(BaseModel):
    """Model for updating course details"""
    course_code: Optional[str] = Field(None, min_length=1, max_length=20, description="Course code")
    course_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Full course name")
    description: Optional[str] = Field(None, max_length=1000, description="Course description")
    credits: Optional[int] = Field(None, ge=1, le=10, description="Credit hours")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    instructor: Optional[str] = Field(None, max_length=100, description="Instructor name")

class CourseResponse(BaseModel):
    """Model for course response data"""
    id: UUID
    course_code: str
    course_name: str
    description: Optional[str] = None
    credits: Optional[int] = None
    department: Optional[str] = None
    instructor: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Enrollment Models (Many-to-Many relationship)
class EnrollmentCreate(BaseModel):
    """Model for creating a new enrollment"""
    user_id: UUID = Field(..., description="ID of the user to enroll")
    course_id: UUID = Field(..., description="ID of the course")
    semester: Optional[str] = Field(None, max_length=20, description="Semester (e.g., Fall, Spring)")
    year: Optional[int] = Field(None, ge=2000, le=2030, description="Academic year")
    grade: Optional[str] = Field(None, max_length=5, description="Grade received (e.g., A, B, C)")

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

# Legacy models for backward compatibility (if needed)
class CourseEnrollment(BaseModel):
    """Legacy model for course enrollment (backward compatibility)"""
    course_code: str = Field(..., min_length=1, max_length=20, description="Course code")
    course_name: str = Field(..., min_length=1, max_length=200, description="Full course name")
    semester: Optional[str] = Field(None, max_length=20, description="Semester")
    year: Optional[int] = Field(None, ge=2000, le=2030, description="Academic year")