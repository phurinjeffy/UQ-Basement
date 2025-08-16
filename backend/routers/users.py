from fastapi import APIRouter, HTTPException, status
import jwt
from datetime import datetime, timedelta, timezone
import os
import httpx
from typing import Optional, List
from models import (
    UserCreate,
    UserLogin,
    UserUpdate,
    PasswordUpdate,
    UserResponse,
    CourseEnrollment,
)
from config import (
    get_supabase_headers,
    SUPABASE_REST_URL,
    hash_password,
    verify_password,
    logger,
)
from uuid import UUID


JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 10800

router = APIRouter()


# Users endpoints
@router.get("/users")
async def get_users():
    """Get all users from the database (passwords excluded)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"select": "id,email,created_at"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}",
                )

            users = response.json()
            logger.info(f"Retrieved {len(users)} users")
            return {"users": users, "count": len(users)}

    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database",
        )
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user in the database with hashed password"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user with email already exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"email": f"eq.{user.email}", "select": "email"},
            )

            if check_response.status_code == 200 and check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

            # Hash the password
            hashed_password = hash_password(user.password)

            # Prepare user data with hashed password (only fields that exist in table)
            user_data = {"email": user.email, "password_hash": hashed_password}

            # Create the user
            create_response = await client.post(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                json=user_data,
            )

            if create_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail=f"Supabase API error: {create_response.text}",
                )

            created_users = create_response.json()
            if not created_users:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user - no data returned",
                )

            created_user = (
                created_users[0] if isinstance(created_users, list) else created_users
            )

            # Remove password_hash from response
            if "password_hash" in created_user:
                del created_user["password_hash"]

            logger.info(
                f"User created successfully: {created_user.get('email', 'unknown')}"
            )

            return {"message": "User created successfully", "user": created_user}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.post("/users/login")
async def login_user(login_data: UserLogin):
    """Authenticate a user with email and password, return JWT token"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user by email (including password_hash)
            response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"email": f"eq.{login_data.email}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}",
                )

            users = response.json()
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            user = users[0]

            # Verify password
            if not verify_password(login_data.password, user.get("password_hash", "")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            # Remove password_hash from response
            if "password_hash" in user:
                del user["password_hash"]

            # Generate JWT token
            payload = {
                "user_id": user["id"],
                "name": user.get("name", user.get("email")),
                "exp": (datetime.now(timezone.utc) + timedelta(seconds=JWT_EXP_DELTA_SECONDS)).timestamp()
            }
            if not JWT_SECRET:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT secret key not set in environment variables."
                )
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            logger.info(f"User logged in successfully: {user['email']}")

            return {
                "message": "Login successful",
                "user": user,
                "token": token
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.get("/users/{user_id}")
async def get_user(user_id: UUID):
    """Get a specific user by ID with their enrolled courses"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user details (only available fields)
            user_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}", "select": "id,email,created_at"},
            )

            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=user_response.status_code,
                    detail=f"Supabase API error: {user_response.text}",
                )

            users = user_response.json()
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            user = users[0]

            # Get user's course enrollments from course table
            try:
                courses_response = await client.get(
                    f"{SUPABASE_REST_URL}/courses",
                    headers=get_supabase_headers(),
                    params={"user_id": f"eq.{user_id}"},
                )

                if courses_response.status_code == 200:
                    user["courses"] = courses_response.json()
                else:
                    user["courses"] = []
            except:
                # If course table doesn't exist, just set empty array
                user["courses"] = []

            return {"user": user}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}",
        )


@router.put("/users/{user_id}")
async def update_user(user_id: UUID, user_update: UserUpdate):
    """Update a user by ID (only email can be updated)"""
    try:
        # Only include non-None values
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update",
            )

        # Check if email already exists for another user
        if "email" in update_data:
            async with httpx.AsyncClient() as client:
                check_response = await client.get(
                    f"{SUPABASE_REST_URL}/users",
                    headers=get_supabase_headers(),
                    params={"email": f"eq.{update_data['email']}", "select": "id"},
                )

                if check_response.status_code == 200:
                    existing_users = check_response.json()
                    if existing_users and existing_users[0]["id"] != str(user_id):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User with this email already exists",
                        )

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"},
                json=update_data,
            )

            if response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}",
                )

            updated_users = response.json() if response.content else []
            if not updated_users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            updated_user = (
                updated_users[0] if isinstance(updated_users, list) else updated_users
            )

            # Remove password_hash from response if present
            if "password_hash" in updated_user:
                del updated_user["password_hash"]

            logger.info(f"User {user_id} updated successfully")

            return {"message": "User updated successfully", "user": updated_user}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.put("/users/{user_id}/password")
async def update_user_password(user_id: UUID, password_data: PasswordUpdate):
    """Update a user's password"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user to verify current password
            get_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"},
            )

            if get_response.status_code != 200:
                raise HTTPException(
                    status_code=get_response.status_code,
                    detail=f"Supabase API error: {get_response.text}",
                )

            users = get_response.json()
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            user = users[0]

            # Verify current password
            if not verify_password(
                password_data.current_password, user.get("password_hash", "")
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect",
                )

            # Hash new password and update
            new_password_hash = hash_password(password_data.new_password)
            update_response = await client.patch(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"},
                json={"password_hash": new_password_hash},
            )

            if update_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=update_response.status_code,
                    detail=f"Supabase API error: {update_response.text}",
                )

            logger.info(f"Password updated successfully for user {user_id}")
            return {"message": "Password updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating password for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}",
        )


@router.delete("/users/{user_id}")
async def delete_user(user_id: UUID):
    """Delete a user by ID"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}", "select": "id"},
            )

            if check_response.status_code == 200 and not check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            # Delete the user (this will cascade delete enrollments if foreign keys are set up)
            delete_response = await client.delete(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"},
            )

            if delete_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=delete_response.status_code,
                    detail=f"Supabase API error: {delete_response.text}",
                )

            logger.info(f"User {user_id} deleted successfully")
            return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


# Course enrollment endpoints (using course table)
@router.post("/users/{user_id}/courses")
async def enroll_user_in_course(user_id: UUID, course: CourseEnrollment):
    """Enroll a user in a course"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user exists
            user_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}", "select": "id"},
            )

            if user_response.status_code != 200 or not user_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            # Check if already enrolled
            existing_enrollment = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={
                    "user_id": f"eq.{user_id}",
                    "course_code": f"eq.{course.course_code}",
                },
            )

            if existing_enrollment.status_code == 200 and existing_enrollment.json():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already enrolled in this course",
                )

            # Create enrollment
            enrollment_data = {
                "user_id": str(user_id),  # Convert UUID to string
                "course_code": course.course_code,
                "course_name": course.course_name,
                "semester": course.semester,
                "year": course.year,
            }

            create_response = await client.post(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                json=enrollment_data,
            )

            if create_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail=f"Supabase API error: {create_response.text}",
                )

            created_enrollment = create_response.json()
            if not created_enrollment:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create enrollment",
                )

            enrollment = (
                created_enrollment[0]
                if isinstance(created_enrollment, list)
                else created_enrollment
            )

            logger.info(f"User {user_id} enrolled in course {course.course_code}")

            return {
                "message": "Successfully enrolled in course",
                "enrollment": enrollment,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling user {user_id} in course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll in course: {str(e)}",
        )


@router.get("/users/{user_id}/courses")
async def get_user_courses(user_id: UUID):
    """Get all courses for a specific user"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user exists
            user_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}", "select": "id,email"},
            )

            if user_response.status_code != 200 or not user_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            user = user_response.json()[0]

            # Get user's courses
            courses_response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"user_id": f"eq.{user_id}"},
            )

            if courses_response.status_code != 200:
                raise HTTPException(
                    status_code=courses_response.status_code,
                    detail=f"Supabase API error: {courses_response.text}",
                )

            courses = courses_response.json()

            return {"user": user, "courses": courses, "count": len(courses)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving courses for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve courses: {str(e)}",
        )


@router.delete("/users/{user_id}/courses/{course_code}")
async def unenroll_user_from_course(user_id: UUID, course_code: str):
    """Remove a user from a course"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if enrollment exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"user_id": f"eq.{user_id}", "course_code": f"eq.{course_code}"},
            )

            if check_response.status_code != 200 or not check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found"
                )

            # Delete enrollment
            delete_response = await client.delete(
                f"{SUPABASE_REST_URL}/courses",
                headers=get_supabase_headers(),
                params={"user_id": f"eq.{user_id}", "course_code": f"eq.{course_code}"},
            )

            if delete_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=delete_response.status_code,
                    detail=f"Supabase API error: {delete_response.text}",
                )

            logger.info(f"User {user_id} unenrolled from course {course_code}")

            return {"message": "Successfully unenrolled from course"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error unenrolling user {user_id} from course {course_code}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unenroll from course: {str(e)}",
        )
