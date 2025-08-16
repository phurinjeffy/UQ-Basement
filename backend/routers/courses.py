from fastapi import APIRouter, HTTPException, status, Query
import httpx
from typing import Optional, List
import urllib.parse
from models import (
    CourseCreate, CourseUpdate, CourseResponse, 
    EnrollmentCreate, EnrollmentResponse,
    UQCourse, SyncResponse, BatchCreateResponse
)
from config import get_supabase_headers, SUPABASE_REST_URL, logger
from uuid import UUID

router = APIRouter()

# Course Management Endpoints
@router.get("/courses")
async def get_courses(
    name: Optional[str] = Query(None, description="Filter courses by course code (name)"),
    campus: Optional[str] = Query(None, description="Filter courses by campus"),
    period: Optional[str] = Query(None, description="Filter courses by period"),
    type: Optional[str] = Query(None, description="Filter courses by type"),
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
                "order": "name.asc"
            }
            
            # Add filters if provided
            if name:
                params["name"] = f"ilike.%{name}%"
            if campus:
                params["campus"] = f"eq.{campus}"
            if period:
                params["period"] = f"eq.{period}"
            if type:
                params["type"] = f"eq.{type}"
            
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
                            "select": "id,user_id,enrolled_at,semester,year,grade"
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
            # Check if course with same name already exists
            existing_course = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={
                    "name": f"eq.{course.name}",
                    "select": "id"
                }
            )
            
            if existing_course.status_code == 200 and existing_course.json():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Course with this name already exists"
                )
            
            # Prepare course data
            course_data = {
                "name": course.name,
                "url": course.url,
                "type": course.type,
                "course_title": course.course_title,
                "campus": course.campus,
                "period": course.period
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
            
            logger.info(f"Course created: {created_course.get('name', 'unknown')}")
            
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
            
            # If updating name, check for duplicates
            if 'name' in update_data:
                duplicate_check = await client.get(
                    f"{SUPABASE_REST_URL}/courses",
                    headers=get_supabase_headers(),
                    params={
                        "name": f"eq.{update_data['name']}",
                        "select": "id"
                    }
                )
                
                if duplicate_check.status_code == 200:
                    duplicates = duplicate_check.json()
                    if duplicates and duplicates[0]['id'] != str(course_id):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Course with this name already exists"
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
                params={"id": f"eq.{course_id}", "select": "id,name"}
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
            
            logger.info(f"Course {course_id} ({course_info['name']}) deleted successfully")
            
            return {
                "message": "Course deleted successfully",
                "deleted_course": {
                    "id": str(course_id),
                    "name": course_info['name']
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

# UQ Library Integration Endpoints
@router.post("/sync-uq-courses", status_code=status.HTTP_201_CREATED)
async def sync_uq_courses(hint: Optional[str] = Query(default=None)):
    """Fetch courses from UQ Library API and sync to Supabase"""
    hint = hint or ""

    if hint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hint parameter must be at least 4 characters long"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch from UQ Library API
            uq_api_url = f"https://api.library.uq.edu.au/v1/learning_resources/suggestions?hint={urllib.parse.quote(hint)}"
            uq_response = await client.get(uq_api_url)
            
            if uq_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"UQ Library API error: {uq_response.status_code}"
                )
            
            uq_courses = uq_response.json()
            
            if not uq_courses:
                return {
                    "message": "No courses found from UQ Library API",
                    "synced_courses": [],
                    "skipped_courses": [],
                    "errors": []
                }
            
            synced_courses = []
            skipped_courses = []
            errors = []
            
            # Process each course from UQ API
            for uq_course in uq_courses:
                try:
                    name = uq_course.get("name", "")
                    url = uq_course.get("url", "")
                    course_type = uq_course.get("type", "")
                    course_title = uq_course.get("course_title", "")
                    campus = uq_course.get("campus", "")
                    period = uq_course.get("period", "")
                    
                    # Skip if essential data is missing
                    if not all([name, url, course_type, course_title, campus, period]):
                        errors.append(f"Skipping course - missing essential data: {uq_course}")
                        continue
                    
                    # Check if course already exists
                    existing_course = await client.get(
                        f"{SUPABASE_REST_URL}/courses",
                        headers=get_supabase_headers(),
                        params={
                            "name": f"eq.{name}",
                            "select": "id,name"
                        }
                    )
                    
                    if existing_course.status_code == 200 and existing_course.json():
                        skipped_courses.append({
                            "name": name,
                            "reason": "Course already exists"
                        })
                        continue
                    
                    # Prepare course data - exact match to UQ API structure
                    course_data = {
                        "name": name,
                        "url": url,
                        "type": course_type,
                        "course_title": course_title,
                        "campus": campus,
                        "period": period
                    }
                    
                    # Create the course in Supabase
                    create_response = await client.post(
                        f"{SUPABASE_REST_URL}/courses",
                        headers=get_supabase_headers(),
                        json=course_data
                    )
                    
                    if create_response.status_code not in [200, 201]:
                        errors.append(f"Failed to create {name}: {create_response.text}")
                        continue
                    
                    created_course_data = create_response.json()
                    created_course = created_course_data[0] if isinstance(created_course_data, list) else created_course_data
                    
                    synced_courses.append({
                        "name": name,
                        "course_title": course_title,
                        "campus": campus,
                        "period": period,
                        "id": created_course.get("id")
                    })
                    
                    logger.info(f"Synced course from UQ Library: {name}")
                    
                except Exception as course_error:
                    errors.append(f"Error processing course {uq_course.get('name', 'unknown')}: {str(course_error)}")
                    continue
            
            return {
                "message": f"Sync completed. {len(synced_courses)} courses added, {len(skipped_courses)} skipped, {len(errors)} errors",
                "synced_courses": synced_courses,
                "skipped_courses": skipped_courses,
                "errors": errors,
                "total_processed": len(uq_courses)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing UQ courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync UQ courses: {str(e)}"
        )

@router.post("/batch-create-courses", status_code=status.HTTP_201_CREATED)
async def batch_create_courses(uq_courses: List[UQCourse]):
    """Create multiple courses from UQ Library API results"""
    try:
        synced_courses = []
        skipped_courses = []
        errors = []
        
        async with httpx.AsyncClient() as client:
            for uq_course in uq_courses:
                try:
                    name = uq_course.name
                    url = uq_course.url
                    course_type = uq_course.type
                    course_title = uq_course.course_title
                    campus = uq_course.campus
                    period = uq_course.period
                    
                    if not all([name, url, course_type, course_title, campus, period]):
                        errors.append(f"Skipping course - missing essential data: {name}")
                        continue
                    
                    # Check if course already exists
                    existing_course = await client.get(
                        f"{SUPABASE_REST_URL}/courses",
                        headers=get_supabase_headers(),
                        params={
                            "name": f"eq.{name}",
                            "select": "id"
                        }
                    )
                    
                    if existing_course.status_code == 200 and existing_course.json():
                        skipped_courses.append({
                            "name": name,
                            "reason": "Already exists"
                        })
                        continue
                    
                    # Create course data - exact match to UQ API
                    course_data = {
                        "name": name,
                        "url": url,
                        "type": course_type,
                        "course_title": course_title,
                        "campus": campus,
                        "period": period
                    }
                    
                    # Create in Supabase
                    create_response = await client.post(
                        f"{SUPABASE_REST_URL}/courses",
                        headers=get_supabase_headers(),
                        json=course_data
                    )
                    
                    if create_response.status_code in [200, 201]:
                        created_course_data = create_response.json()
                        created_course = created_course_data[0] if isinstance(created_course_data, list) else created_course_data
                        synced_courses.append({
                            "name": name,
                            "course_title": course_title,
                            "campus": campus,
                            "period": period,
                            "id": created_course.get("id")
                        })
                    else:
                        errors.append(f"Failed to create {name}: {create_response.text}")
                        
                except Exception as course_error:
                    errors.append(f"Error processing {name}: {str(course_error)}")
        
        return {
            "message": f"Batch processing completed. {len(synced_courses)} created, {len(skipped_courses)} skipped, {len(errors)} errors",
            "synced_courses": synced_courses,
            "skipped_courses": skipped_courses,
            "errors": errors,
            "total_processed": len(uq_courses)
        }
        
    except Exception as e:
        logger.error(f"Error in batch create: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch create failed: {str(e)}"
        )