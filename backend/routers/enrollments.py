from fastapi import APIRouter, HTTPException, status, Query
import httpx
from typing import Optional
from models import (
    EnrollmentCreate
)
from config import get_supabase_headers, SUPABASE_REST_URL, logger
from uuid import UUID

router = APIRouter()

# Enrollment Management Endpoints (Many-to-Many relationship)
@router.post("/enrollments", status_code=status.HTTP_201_CREATED)
async def create_enrollment(enrollment: EnrollmentCreate):
    """Enroll a user in a course"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user exists
            user_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{enrollment.user_id}", "select": "id"}
            )
            
            if user_response.status_code != 200 or not user_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if course exists
            course_response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"id": f"eq.{enrollment.course_id}", "select": "id,name,course_title"}
            )
            
            if course_response.status_code != 200 or not course_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            course_info = course_response.json()[0]
            
            # Check if user is already enrolled in this course
            existing_enrollment = await client.get(
                f"{SUPABASE_REST_URL}/enrollments",
                headers=get_supabase_headers(),
                params={
                    "user_id": f"eq.{enrollment.user_id}",
                    "course_id": f"eq.{enrollment.course_id}"
                }
            )
            
            if existing_enrollment.status_code == 200 and existing_enrollment.json():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already enrolled in this course"
                )
            
            # Create enrollment
            enrollment_data = {
                "user_id": str(enrollment.user_id),
                "course_id": str(enrollment.course_id),
                "semester": enrollment.semester,
                "year": enrollment.year,
                "grade": enrollment.grade
            }
            
            create_response = await client.post(
                f"{SUPABASE_REST_URL}/enrollments",
                headers=get_supabase_headers(),
                json=enrollment_data
            )
            
            if create_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail=f"Supabase API error: {create_response.text}"
                )
            
            created_enrollment = create_response.json()
            if not created_enrollment:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create enrollment"
                )
            
            enrollment_result = created_enrollment[0] if isinstance(created_enrollment, list) else created_enrollment
            
            # Add course info to response
            enrollment_result['course'] = course_info
            
            logger.info(f"User {enrollment.user_id} enrolled in course {course_info['name']}")
            
            return {
                "message": "Successfully enrolled in course",
                "enrollment": enrollment_result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating enrollment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enrollment: {str(e)}"
        )

@router.get("/enrollments")
async def get_enrollments(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    course_id: Optional[UUID] = Query(None, description="Filter by course ID"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get enrollments with optional filtering"""
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "select": "*",
                "limit": str(limit),
                "offset": str(offset)
            }
            
            # Add filters if provided
            if user_id:
                params["user_id"] = f"eq.{user_id}"
            if course_id:
                params["course_id"] = f"eq.{course_id}"
            if semester:
                params["semester"] = f"eq.{semester}"
            if year:
                params["year"] = f"eq.{year}"
            
            response = await client.get(
                f"{SUPABASE_REST_URL}/enrollments",
                headers=get_supabase_headers(),
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            enrollments = response.json()
            
            # Enrich with user and course data
            for enrollment in enrollments:
                # Get user info
                user_response = await client.get(
                    f"{SUPABASE_REST_URL}/users",
                    headers=get_supabase_headers(),
                    params={"id": f"eq.{enrollment['user_id']}", "select": "id,email"}
                )
                if user_response.status_code == 200:
                    users = user_response.json()
                    if users:
                        enrollment['user'] = users[0]
                
                # Get course info
                course_response = await client.get(
                    f"{SUPABASE_REST_URL}/courses",
                    headers=get_supabase_headers(),
                    params={"id": f"eq.{enrollment['course_id']}", "select": "id,name,course_title"}
                )
                if course_response.status_code == 200:
                    courses = course_response.json()
                    if courses:
                        enrollment['course'] = courses[0]
            
            return {
                "enrollments": enrollments,
                "count": len(enrollments),
                "limit": limit,
                "offset": offset
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving enrollments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve enrollments: {str(e)}"
        )

@router.delete("/enrollments/{enrollment_id}")
async def delete_enrollment(enrollment_id: UUID):
    """Remove an enrollment"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if enrollment exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/enrollments",
                headers=get_supabase_headers(),
                params={"id": f"eq.{enrollment_id}", "select": "*"}
            )
            
            if check_response.status_code != 200 or not check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Enrollment not found"
                )
            
            enrollment_info = check_response.json()[0]
            
            # Delete enrollment
            delete_response = await client.delete(
                f"{SUPABASE_REST_URL}/enrollments",
                headers=get_supabase_headers(),
                params={"id": f"eq.{enrollment_id}"}
            )
            
            if delete_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=delete_response.status_code,
                    detail=f"Supabase API error: {delete_response.text}"
                )
            
            logger.info(f"Enrollment {enrollment_id} deleted successfully")
            
            return {
                "message": "Enrollment deleted successfully",
                "deleted_enrollment": {
                    "id": str(enrollment_id),
                    "user_id": enrollment_info['user_id'],
                    "course_id": enrollment_info['course_id']
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting enrollment {enrollment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete enrollment: {str(e)}"
        )