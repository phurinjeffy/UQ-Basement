from fastapi import FastAPI
from routers import users

# Initialize FastAPI app
app = FastAPI(
    title="Users API",
    description="A simple users management API with Supabase backend",
    version="1.0.0"
)

# Include routers
app.include_router(users.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Users API is running", "version": "1.0.0"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "users-api"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)