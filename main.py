"""FastAPI Healthcare Skill Intelligence System"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
from datetime import datetime

from app.database import get_db, init_db
from app import schemas

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Skill Intelligence API",
    description="AI-powered skill gap analysis for healthcare professionals",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== STARTUP EVENT =====
@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()
    print("✅ FastAPI server started successfully!")


# ===== ROOT ENDPOINT =====
@app.get("/")
def read_root():
    """Root endpoint - API health check."""
    return {
        "status": "online",
        "message": "Healthcare Skill Intelligence API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "users": "/api/users",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}


# ===== USER ENDPOINTS =====
@app.post("/api/users/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate):
    """
    Register a new user.
    
    - **name**: User's full name
    - **email**: User's email (must be unique)
    - **education**: Degree and major
    - **target_role**: Target healthcare role
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (name, email, education, university, graduation_year, location, 
                             target_role, target_sector, phone, linkedin_url, github_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user.name, user.email, user.education, user.university, user.graduation_year,
              user.location, user.target_role, user.target_sector, user.phone, 
              user.linkedin_url, user.github_url))
        
        user_id = cursor.lastrowid
        
        # Get created user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        return dict(row)


@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int):
    """Get user by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        return dict(row)


@app.get("/api/users/{user_id}/profile", response_model=schemas.ProfileSummary)
def get_user_profile(user_id: int):
    """Get complete user profile with statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Count related items
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE user_id = ?", (user_id,))
        total_courses = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE user_id = ?", (user_id,))
        total_projects = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM certifications WHERE user_id = ?", (user_id,))
        total_certifications = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM work_experience WHERE user_id = ?", (user_id,))
        total_work_experience = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM user_skills WHERE user_id = ?", (user_id,))
        total_skills = cursor.fetchone()['count']
        
        user = dict(user_row)
        
        # Calculate profile completion
        fields_filled = sum([
            bool(user.get('name')),
            bool(user.get('email')),
            bool(user.get('education')),
            bool(user.get('location')),
            bool(user.get('target_role')),
            total_courses > 0,
            total_projects > 0,
        ])
        profile_completion = round((fields_filled / 7) * 100, 1)
        
        return {
            "user": user,
            "total_courses": total_courses,
            "total_projects": total_projects,
            "total_certifications": total_certifications,
            "total_work_experience": total_work_experience,
            "total_skills": total_skills,
            "profile_completion": profile_completion
        }


@app.get("/api/users", response_model=List[schemas.UserResponse])
def list_users(skip: int = 0, limit: int = 100):
    """List all users."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ===== COURSE ENDPOINTS =====
@app.post("/api/users/{user_id}/courses", response_model=schemas.CourseResponse)
def add_course(user_id: int, course: schemas.CourseCreate):
    """Add a course for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Insert course
        cursor.execute('''
            INSERT INTO courses (user_id, course_name, platform, instructor, grade, 
                               completion_date, duration, description, certificate_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, course.course_name, course.platform, course.instructor, 
              course.grade, course.completion_date, course.duration, 
              course.description, course.certificate_url))
        
        course_id = cursor.lastrowid
        
        # Get created course
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        if result.get('skills_extracted'):
            result['skills_extracted'] = json.loads(result['skills_extracted'])
        
        return result


@app.get("/api/users/{user_id}/courses", response_model=List[schemas.CourseResponse])
def get_user_courses(user_id: int):
    """Get all courses for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get courses
        cursor.execute("SELECT * FROM courses WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        courses = []
        for row in rows:
            course = dict(row)
            if course.get('skills_extracted'):
                course['skills_extracted'] = json.loads(course['skills_extracted'])
            courses.append(course)
        
        return courses


# ===== PROJECT ENDPOINTS =====
@app.post("/api/users/{user_id}/projects", response_model=schemas.ProjectResponse)
def add_project(user_id: int, project: schemas.ProjectCreate):
    """Add a project for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Insert project
        tech_stack_json = json.dumps(project.tech_stack) if project.tech_stack else None
        
        cursor.execute('''
            INSERT INTO projects (user_id, project_name, description, tech_stack, role, 
                                team_size, duration, github_link, deployed_link, 
                                project_type, impact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, project.project_name, project.description, tech_stack_json,
              project.role, project.team_size, project.duration, project.github_link,
              project.deployed_link, project.project_type, project.impact))
        
        project_id = cursor.lastrowid
        
        # Get created project
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        if result.get('tech_stack'):
            result['tech_stack'] = json.loads(result['tech_stack'])
        if result.get('skills_extracted'):
            result['skills_extracted'] = json.loads(result['skills_extracted'])
        
        return result


@app.get("/api/users/{user_id}/projects", response_model=List[schemas.ProjectResponse])
def get_user_projects(user_id: int):
    """Get all projects for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get projects
        cursor.execute("SELECT * FROM projects WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            project = dict(row)
            if project.get('tech_stack'):
                project['tech_stack'] = json.loads(project['tech_stack'])
            if project.get('skills_extracted'):
                project['skills_extracted'] = json.loads(project['skills_extracted'])
            projects.append(project)
        
        return projects


# ===== SKILL ENDPOINTS =====
@app.get("/api/users/{user_id}/skills", response_model=List[schemas.UserSkillResponse])
def get_user_skills(user_id: int):
    """Get all extracted skills for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get skills
        cursor.execute("SELECT * FROM user_skills WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        skills = []
        for row in rows:
            skill = dict(row)
            if skill.get('sources'):
                skill['sources'] = json.loads(skill['sources'])
            skills.append(skill)
        
        return skills


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Healthcare Skill Intelligence API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
