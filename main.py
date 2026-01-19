"""FastAPI Healthcare Skill Intelligence System - Clean Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import (
    users_router,
    courses_router,
    projects_router,
    skills_router,
    resume_router,
    jobs_router,
    analysis_router,
    roadmaps_router
)

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Skill Intelligence API",
    description="""
    AI-powered skill gap analysis for healthcare professionals.
    
    ## Features
    - **User Management**: Register and manage user profiles
    - **Resume Processing**: Upload and parse resumes to extract skills
    - **Course Management**: Track completed courses
    - **Project Management**: Document projects and tech stack
    - **Skill Extraction**: NLP-based skill extraction from all sources
    - **Job Search**: Search LinkedIn for healthcare jobs
    - **Gap Analysis**: Compare skills against market requirements
    - **Course Recommendations**: AI-powered course suggestions
    - **GitHub Analysis**: Extract skills from repositories
    
    ## Workflow
    1. Register user -> 2. Upload resume -> 3. Extract skills -> 4. Gap analysis -> 5. Get recommendations
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== STARTUP EVENT =====
@app.on_event("startup")
def startup_event():
    """Initialize database and services on startup."""
    init_db()
    # Trigger service initialization
    from app.routers.dependencies import get_services
    get_services()
    print("FastAPI server started successfully!")


# ===== HEALTH & ROOT ENDPOINTS =====
@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint - API health check and info."""
    return {
        "status": "online",
        "message": "Healthcare Skill Intelligence API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "users": "/api/users",
            "skills": "/api/skills",
            "jobs": "/api/jobs",
            "analysis": "/api/users/{user_id}/gap-analysis",
            "courses": "/api/courses/search/{skill}"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "database": "connected",
        "services": "initialized"
    }


# ===== REGISTER ROUTERS =====
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(projects_router)
app.include_router(skills_router)
app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(analysis_router)
app.include_router(roadmaps_router)


# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    import uvicorn
    print("Starting Healthcare Skill Intelligence API...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
