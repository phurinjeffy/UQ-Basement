from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

class CourseEnrollment(BaseModel):
    course_code: str
    course_name: str
    semester: str
    year: int

class CourseEnrollmentResponse(CourseEnrollment):
    id: str
    user_id: str
    enrolled_at: datetime