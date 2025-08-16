from fastapi import FastAPI
from routers import users, courses, ai, questions, enrollments, quiz, answers

# Initialize FastAPI app
app = FastAPI(
    title="Users API",
    description="A simple users management API with Supabase backend",
    version="1.0.0",
)

# Include routers
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(courses.router, prefix="/api/v1", tags=["Courses"])
app.include_router(ai.router, prefix="/api/v1", tags=["AI"])
app.include_router(questions.router, prefix="/api/v1", tags=["Questions"])
app.include_router(enrollments.router, prefix="/api/v1", tags=["Enrollments"])
app.include_router(quiz.router, prefix="/api/v1", tags=["Quiz"])
app.include_router(answers.router, prefix="/api/v1", tags=["Answers"])

# CORS middleware setup
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Range"],  # Explicitly allow Range header for PDF streaming
)

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
