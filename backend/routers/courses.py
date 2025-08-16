from fastapi import APIRouter, HTTPException, status, Query
import httpx
from typing import Optional, List
from models import CourseCreate, CourseUpdate, CourseResponse, EnrollmentCreate, EnrollmentResponse
from config import get_supabase_headers, SUPABASE_REST_URL, logger
from uuid import UUID

router = APIRouter()

# Course Management Endpoints (Independent of users)
@router.get("/courses")
async def get_courses(
    course_code: Optional[str] = Query(None, description="Filter courses by course code"),
    department: Optional[str] = Query(None, description="Filter courses by department"),
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    include_enrollment_count: bool = Query(False, description="Include enrollment count for each course")
):
    """Get all courses with optional filtering"""
    try:
        async with httpx.AsyncClient() as client:
            # Build query parameters
            params = {
                "select": "*",
                "limit": str(limit),
                "offset": str(offset),
                "order": "course_code.asc"
            }
            
            # Add filters if provided
            if course_code:
                params["course_code"] = f"eq.{course_code}"
            if department:
                params["department"] = f"eq.{department}"
            
            response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params=params
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            courses = response.json()
            
            # Optionally include enrollment count
            if include_enrollment_count:
                for course in courses:
                    try:
                        enrollment_response = await client.get(
                            f"{SUPABASE_REST_URL}/enrollments",
                            headers=get_supabase_headers(),
                            params={
                                "course_id": f"eq.{course['id']}",
                                "select": "id"
                            }
                        )
                        if enrollment_response.status_code == 200:
                            enrollments = enrollment_response.json()
                            course['enrollment_count'] = len(enrollments)
                        else:
                            course['enrollment_count'] = 0
                    except Exception:
                        course['enrollment_count'] = 0
            
            logger.info(f"Retrieved {len(courses)} courses")
            
            return {
                "courses": courses,
                "count": len(courses),
                "limit": limit,
                "offset": offset
            }
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error retrieving courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve courses: {str(e)}"
        )

@router.get("/courses/{course_id}")
async def get_course(course_id: UUID, include_enrollments: bool = Query(False, description="Include enrolled users")):
    """Get a specific course by ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={
                    "id": f"eq.{course_id}",
                    "select": "*"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            courses = response.json()
            if not courses:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            course = courses[0]
            
            # Optionally include enrolled users
            if include_enrollments:
                try:
                    enrollment_response = await client.get(
                        f"{SUPABASE_REST_URL}/enrollments",
                        headers=get_supabase_headers(),
                        params={
                            "course_id": f"eq.{course_id}",
                            "select": "id,user_id,enrolled_at,semester,year"
                        }
                    )
                    
                    if enrollment_response.status_code == 200:
                        enrollments = enrollment_response.json()
                        
                        # Get user details for each enrollment
                        for enrollment in enrollments:
                            user_response = await client.get(
                                f"{SUPABASE_REST_URL}/users",
                                headers=get_supabase_headers(),
                                params={
                                    "id": f"eq.{enrollment['user_id']}",
                                    "select": "id,email"
                                }
                            )
                            if user_response.status_code == 200:
                                users = user_response.json()
                                if users:
                                    enrollment['user'] = users[0]
                        
                        course['enrollments'] = enrollments
                        course['enrollment_count'] = len(enrollments)
                    else:
                        course['enrollments'] = []
                        course['enrollment_count'] = 0
                except Exception:
                    course['enrollments'] = []
                    course['enrollment_count'] = 0
            
            return {"course": course}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve course: {str(e)}"
        )

@router.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(course: CourseCreate):
    """Create a new course"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if course with same code already exists
            existing_course = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={
                    "course_code": f"eq.{course.course_code}",
                    "select": "id"
                }
            )
            
            if existing_course.status_code == 200 and existing_course.json():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Course with this code already exists"
                )
            
            # Prepare course data
            course_data = {
                "course_code": course.course_code,
                "course_name": course.course_name,
                "description": course.description,
                "credits": course.credits,
                "department": course.department,
                "instructor": course.instructor
            }
            
            # Create the course
            create_response = await client.post(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                json=course_data
            )
            
            if create_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail=f"Supabase API error: {create_response.text}"
                )
            
            created_courses = create_response.json()
            if not created_courses:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create course - no data returned"
                )
            
            created_course = created_courses[0] if isinstance(created_courses, list) else created_courses
            
            logger.info(f"Course created: {created_course.get('course_code', 'unknown')}")
            
            return {
                "message": "Course created successfully",
                "course": created_course
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {str(e)}"
        )

@router.put("/courses/{course_id}")
async def update_course(course_id: UUID, course_update: CourseUpdate):
    """Update a course by ID"""
    try:
        # Only include non-None values
        update_data = {k: v for k, v in course_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        async with httpx.AsyncClient() as client:
            # Check if course exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"id": f"eq.{course_id}", "select": "*"}
            )
            
            if check_response.status_code != 200 or not check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            # If updating course_code, check for duplicates
            if 'course_code' in update_data:
                duplicate_check = await client.get(
                    f"{SUPABASE_REST_URL}/courses",
                    headers=get_supabase_headers(),
                    params={
                        "course_code": f"eq.{update_data['course_code']}",
                        "select": "id"
                    }
                )
                
                if duplicate_check.status_code == 200:
                    duplicates = duplicate_check.json()
                    if duplicates and duplicates[0]['id'] != str(course_id):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Course with this code already exists"
                        )
            
            # Update the course
            response = await client.patch(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"id": f"eq.{course_id}"},
                json=update_data
            )
            
            if response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            updated_courses = response.json() if response.content else []
            if not updated_courses:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            updated_course = updated_courses[0] if isinstance(updated_courses, list) else updated_courses
            
            logger.info(f"Course {course_id} updated successfully")
            
            return {
                "message": "Course updated successfully",
                "course": updated_course
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course: {str(e)}"
        )

@router.delete("/courses/{course_id}")
async def delete_course(course_id: UUID, force: bool = Query(False, description="Force delete even if users are enrolled")):
    """Delete a course by ID"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if course exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"id": f"eq.{course_id}", "select": "id,course_code"}
            )
            
            if check_response.status_code != 200 or not check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            
            course_info = check_response.json()[0]
            
            # Check for existing enrollments
            enrollments_response = await client.get(
                f"{SUPABASE_REST_URL}/enrollments",
                headers=get_supabase_headers(),
                params={"course_id": f"eq.{course_id}", "select": "id"}
            )
            
            if enrollments_response.status_code == 200:
                enrollments = enrollments_response.json()
                if enrollments and not force:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot delete course with {len(enrollments)} active enrollments. Use force=true to override."
                    )
                
                # If force=true, delete all enrollments first
                if enrollments and force:
                    await client.delete(
                        f"{SUPABASE_REST_URL}/enrollments",
                        headers=get_supabase_headers(),
                        params={"course_id": f"eq.{course_id}"}
                    )
            
            # Delete the course
            delete_response = await client.delete(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"id": f"eq.{course_id}"}
            )
            
            if delete_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=delete_response.status_code,
                    detail=f"Supabase API error: {delete_response.text}"
                )
            
            logger.info(f"Course {course_id} ({course_info['course_code']}) deleted successfully")
            
            return {
                "message": "Course deleted successfully",
                "deleted_course": {
                    "id": str(course_id),
                    "course_code": course_info['course_code']
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete course: {str(e)}"
        )

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
                params={"id": f"eq.{enrollment.course_id}", "select": "id,course_code,course_name"}
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
            
            logger.info(f"User {enrollment.user_id} enrolled in course {course_info['course_code']}")
            
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
                    params={"id": f"eq.{enrollment['course_id']}", "select": "id,course_code,course_name"}
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