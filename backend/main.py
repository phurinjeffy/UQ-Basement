from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional
import logging
import httpx
import json
from passlib.context import CryptContext
from passlib.hash import bcrypt

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Supabase REST API endpoints
SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1"

# Headers for Supabase API requests
def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# Initialize FastAPI app
app = FastAPI(
    title="User Management API",
    description="API for managing users with Supabase REST API and password hashing",
    version="1.0.0"
)

# Pydantic models for request/response
class UserCreate(BaseModel):
    email: str
    password: str  # Plain password - will be hashed before storing

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123"
            }
        }

class UserLogin(BaseModel):
    email: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123"
            }
        }

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int]
    phone: Optional[str]
    created_at: str
    # Note: password_hash is excluded from response for security

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@app.get("/")
async def root():
    return {"message": "FastAPI + Supabase REST API User Management with Password Hashing is working!"}

@app.get("/users")
async def get_users():
    """Get all users from the database (passwords excluded)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"select": "id,name,email,age,phone,created_at"}  # Exclude password_hash
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            users = response.json()
            logger.info(f"Retrieved {len(users)} users")
            return {"users": users, "count": len(users)}
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user in the database with hashed password (email and password only)"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user with email already exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"email": f"eq.{user.email}", "select": "email"}
            )
            if check_response.status_code == 200 and check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            # Hash the password
            hashed_password = hash_password(user.password)
            # Prepare user data with hashed password (only email and password_hash)
            user_data = {
                "email": user.email,
                "password_hash": hashed_password
            }
            # Create the user
            create_response = await client.post(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                json=user_data
            )
            if create_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail=f"Supabase API error: {create_response.text}"
                )
            created_users = create_response.json()
            if not created_users:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user - no data returned"
                )
            created_user = created_users[0] if isinstance(created_users, list) else created_users
            # Remove password_hash from response
            if 'password_hash' in created_user:
                del created_user['password_hash']
            logger.info(f"User created successfully: {created_user.get('email', 'unknown')}")
            return {
                "message": "User created successfully",
                "user": created_user
            }
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@app.post("/users/login")
async def login_user(login_data: UserLogin):
    """Authenticate a user with email and password"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user by email (including password_hash)
            response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"email": f"eq.{login_data.email}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            users = response.json()
            
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            user = users[0]
            
            # Verify password
            if not verify_password(login_data.password, user.get('password_hash', '')):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Remove password_hash from response
            if 'password_hash' in user:
                del user['password_hash']
            
            logger.info(f"User logged in successfully: {user['email']}")
            
            return {
                "message": "Login successful",
                "user": user
            }
            
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by ID (password excluded)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={
                    "id": f"eq.{user_id}",
                    "select": "id,name,email,age,phone,created_at"  # Exclude password_hash
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            users = response.json()
            
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return {"user": users[0]}
            
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )

@app.put("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate):
    """Update a user by ID (excluding password)"""
    try:
        # Only include non-None values
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        async with httpx.AsyncClient() as client:
            # Update the user
            response = await client.patch(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"},
                json=update_data
            )
            
            if response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Supabase API error: {response.text}"
                )
            
            updated_users = response.json() if response.content else []
            
            if not updated_users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            updated_user = updated_users[0] if isinstance(updated_users, list) else updated_users
            
            # Remove password_hash from response if present
            if 'password_hash' in updated_user:
                del updated_user['password_hash']
                
            logger.info(f"User {user_id} updated successfully")
            
            return {
                "message": "User updated successfully",
                "user": updated_user
            }
            
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@app.put("/users/{user_id}/password")
async def update_user_password(user_id: int, password_data: PasswordUpdate):
    """Update a user's password"""
    try:
        async with httpx.AsyncClient() as client:
            # First, get the user to verify current password
            get_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"}
            )
            
            if get_response.status_code != 200:
                raise HTTPException(
                    status_code=get_response.status_code,
                    detail=f"Supabase API error: {get_response.text}"
                )
            
            users = get_response.json()
            
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user = users[0]
            
            # Verify current password
            if not verify_password(password_data.current_password, user.get('password_hash', '')):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
            
            # Hash new password
            new_password_hash = hash_password(password_data.new_password)
            
            # Update password
            update_response = await client.patch(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"},
                json={"password_hash": new_password_hash}
            )
            
            if update_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=update_response.status_code,
                    detail=f"Supabase API error: {update_response.text}"
                )
            
            logger.info(f"Password updated successfully for user {user_id}")
            
            return {"message": "Password updated successfully"}
            
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error updating password for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update password: {str(e)}"
        )

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user by ID"""
    try:
        async with httpx.AsyncClient() as client:
            # Check if user exists
            check_response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}", "select": "id"}
            )
            
            if check_response.status_code == 200 and not check_response.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Delete the user
            delete_response = await client.delete(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"id": f"eq.{user_id}"}
            )
            
            if delete_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=delete_response.status_code,
                    detail=f"Supabase API error: {delete_response.text}"
                )
            
            logger.info(f"User {user_id} deleted successfully")
            return {"message": "User deleted successfully"}
            
    except HTTPException:
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to database"
        )
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_REST_URL}/users",
                headers=get_supabase_headers(),
                params={"limit": "1", "select": "id"}
            )
            
            if response.status_code == 200:
                return {"status": "healthy", "database": "connected"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Database connection failed: {response.text}"
                )
                
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )