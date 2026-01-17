"""FastAPI Healthcare Skill Intelligence System"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from app.database import get_db, init_db
from app import schemas
from app.services.skill_extractor import SkillExtractor
from app.services.resume_parser import ResumeParser
from app.services.linkedin_job_fetcher import LinkedInJobFetcher
from app.services.job_skill_analyzer import JobSkillAnalyzer
from app.services.gap_analyzer import GapAnalyzer
from app.services.course_recommender import CourseRecommender
from app.services.github_analyzer import GitHubAnalyzer

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Debug: Print if API keys are loaded
print(f"🔑 RAPIDAPI_KEY loaded: {'Yes' if os.getenv('RAPIDAPI_KEY') else 'No'}")
print(f"🔑 TAVILY_API_KEY loaded: {'Yes' if os.getenv('TAVILY_API_KEY') else 'No'}")

# Create uploads directory
UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize skill extractor and resume parser
SKILLS_FILE = os.path.join("app", "data", "healthcare_skills.json")
skill_extractor = SkillExtractor(SKILLS_FILE)
resume_parser = ResumeParser()

# Initialize other services
linkedin_api_key = os.getenv("RAPIDAPI_KEY", "")
tavily_api_key = os.getenv("TAVILY_API_KEY", "")

linkedin_fetcher = LinkedInJobFetcher(linkedin_api_key) if linkedin_api_key else None
job_analyzer = JobSkillAnalyzer(skill_extractor)
gap_analyzer = GapAnalyzer()
course_recommender = CourseRecommender(tavily_api_key)
github_analyzer = GitHubAnalyzer(skill_extractor)

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
        
        user = dict(row)
        user['has_resume'] = bool(user.get('resume_path'))
        return user


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
        user['has_resume'] = bool(user.get('resume_path'))
        
        # Calculate profile completion
        fields_filled = sum([
            bool(user.get('name')),
            bool(user.get('email')),
            bool(user.get('education')),
            bool(user.get('location')),
            bool(user.get('target_role')),
            bool(user.get('resume_path')),
            total_courses > 0,
            total_projects > 0,
        ])
        profile_completion = round((fields_filled / 8) * 100, 1)
        
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


# ===== RESUME ENDPOINTS =====
@app.post("/api/users/{user_id}/upload-resume")
async def upload_resume(user_id: int, file: UploadFile = File(...)):
    """
    Upload resume file for a user.
    Supports: PDF, TXT, DOCX
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.docx', '.doc']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        safe_filename = f"user_{user_id}_resume{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Update database
        cursor.execute(
            "UPDATE users SET resume_path = ? WHERE id = ?",
            (file_path, user_id)
        )
        
        return {
            "message": "Resume uploaded successfully",
            "user_id": user_id,
            "filename": safe_filename,
            "file_path": file_path,
            "file_size": len(content)
        }


@app.post("/api/users/{user_id}/upload-resume-text")
def upload_resume_text(user_id: int, resume_data: schemas.ResumeUpload):
    """
    Upload resume as text (for copy-paste functionality).
    Useful when users don't have resume file or want to paste content directly.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Save resume text to file
        safe_filename = f"user_{user_id}_resume.txt"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(resume_data.resume_text)
        
        # Update database with both path and text
        cursor.execute(
            "UPDATE users SET resume_path = ?, resume_text = ? WHERE id = ?",
            (file_path, resume_data.resume_text, user_id)
        )
        
        return {
            "message": "Resume text uploaded successfully",
            "user_id": user_id,
            "filename": safe_filename,
            "text_length": len(resume_data.resume_text)
        }


@app.get("/api/users/{user_id}/resume-text")
def get_resume_text(user_id: int):
    """Get resume text for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT resume_text, resume_path FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        resume_text = row['resume_text']
        resume_path = row['resume_path']
        
        if not resume_text and not resume_path:
            raise HTTPException(status_code=404, detail="No resume found for this user")
        
        # If we have text, return it
        if resume_text:
            return {
                "user_id": user_id,
                "resume_text": resume_text,
                "source": "database"
            }
        
        # If we only have file path, try to read it
        if resume_path and os.path.exists(resume_path):
            try:
                with open(resume_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {
                    "user_id": user_id,
                    "resume_text": content,
                    "source": "file",
                    "file_path": resume_path
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading resume: {str(e)}")
        
        raise HTTPException(status_code=404, detail="Resume file not found")


# ===== SKILL EXTRACTION ENDPOINTS =====
@app.post("/api/skills/extract/{user_id}")
def extract_user_skills(user_id: int):
    """
    Extract skills from all user data sources (resume, courses, projects).
    Also parses resume structure to extract and save projects, experience, certifications.
    This is the core ML/NLP component!
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = dict(user)
        all_skill_sources = []
        extracted_data = {"projects": 0, "experience": 0, "certifications": 0}
        
        # 1. Parse Resume Structure and Extract Data
        resume_path = user_dict.get('resume_path')
        resume_text = user_dict.get('resume_text')
        
        if resume_path and os.path.exists(resume_path):
            print(f"📄 Extracting text from resume file: {resume_path}")
            resume_text = skill_extractor.extract_text_from_file(resume_path)
        
        if resume_text:
            print("🔍 Parsing resume structure...")
            parsed_resume = resume_parser.parse_resume(resume_text)
            
            # Save extracted projects to database
            if parsed_resume.get('projects'):
                print(f"📋 Found {len(parsed_resume['projects'])} projects in resume")
                for project_data in parsed_resume['projects']:
                    # Check if project already exists
                    cursor.execute(
                        "SELECT id FROM projects WHERE user_id = ? AND project_name = ?",
                        (user_id, project_data['project_name'])
                    )
                    existing = cursor.fetchone()
                    
                    if not existing:
                        tech_stack_json = json.dumps(project_data['tech_stack'])
                        cursor.execute("""
                            INSERT INTO projects 
                            (user_id, project_name, description, tech_stack, role, 
                             github_link, deployed_link, project_type, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id, project_data['project_name'], project_data['description'],
                            tech_stack_json, project_data['role'], project_data['github_link'],
                            project_data['deployed_link'], project_data['project_type'],
                            datetime.now().isoformat()
                        ))
                        extracted_data['projects'] += 1
                        print(f"   ✅ Saved project: {project_data['project_name']}")
            
            # Save extracted work experience to database
            if parsed_resume.get('experience'):
                print(f"💼 Found {len(parsed_resume['experience'])} work experiences in resume")
                for exp_data in parsed_resume['experience']:
                    # Check if experience already exists
                    cursor.execute(
                        "SELECT id FROM work_experience WHERE user_id = ? AND company_name = ? AND job_title = ?",
                        (user_id, exp_data['company_name'], exp_data['job_title'])
                    )
                    existing = cursor.fetchone()
                    
                    if not existing:
                        tech_json = json.dumps(exp_data['technologies_used'])
                        cursor.execute("""
                            INSERT INTO work_experience 
                            (user_id, company_name, job_title, employment_type, start_date,
                             end_date, location, description, technologies_used, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user_id, exp_data['company_name'], exp_data['job_title'],
                            exp_data['employment_type'], exp_data['start_date'],
                            exp_data['end_date'], exp_data['location'], exp_data['description'],
                            tech_json, datetime.now().isoformat()
                        ))
                        extracted_data['experience'] += 1
                        print(f"   ✅ Saved experience: {exp_data['job_title']} at {exp_data['company_name']}")
            
            # Save extracted certifications to database
            if parsed_resume.get('certifications'):
                print(f"🎓 Found {len(parsed_resume['certifications'])} certifications in resume")
                for cert_data in parsed_resume['certifications']:
                    # Check if certification already exists
                    cursor.execute(
                        "SELECT id FROM certifications WHERE user_id = ? AND certification_name = ?",
                        (user_id, cert_data['certification_name'])
                    )
                    existing = cursor.fetchone()
                    
                    if not existing:
                        cursor.execute("""
                            INSERT INTO certifications 
                            (user_id, certification_name, issuing_organization, issue_date,
                             credential_url, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            user_id, cert_data['certification_name'],
                            cert_data['issuing_organization'], cert_data['issue_date'],
                            cert_data['credential_url'], datetime.now().isoformat()
                        ))
                        extracted_data['certifications'] += 1
                        print(f"   ✅ Saved certification: {cert_data['certification_name']}")
            
            conn.commit()
            
            # Extract skills directly from resume structure (no JSON matching)
            print("🔎 Extracting skills from resume...")
            resume_skills = skill_extractor.extract_skills_from_resume(resume_text)
            print(f"   Found {len(resume_skills)} skills in resume")
            
            resume_skill_data = {}
            for skill in resume_skills:
                prof, conf = skill_extractor.calculate_proficiency_from_text(skill, resume_text)
                resume_skill_data[skill] = (prof, conf)
            
            if resume_skill_data:
                all_skill_sources.append({
                    'source': 'resume',
                    'source_id': 0,
                    'skills': resume_skill_data
                })
        
        # 2. Extract from Courses
        cursor.execute("SELECT * FROM courses WHERE user_id = ?", (user_id,))
        courses = cursor.fetchall()
        
        print(f"📚 Processing {len(courses)} courses...")
        for course in courses:
            course_dict = dict(course)
            text = f"{course_dict.get('course_name', '')} {course_dict.get('description', '')}"
            
            course_skills = skill_extractor.extract_skills_from_text(text)
            print(f"   Course '{course_dict.get('course_name', '')[:30]}...': {len(course_skills)} skills")
            
            course_skill_data = {}
            for skill in course_skills:
                prof, conf = skill_extractor.calculate_proficiency_from_course(skill, course_dict)
                course_skill_data[skill] = (prof, conf)
            
            if course_skill_data:
                # Update course with extracted skills
                cursor.execute(
                    "UPDATE courses SET skills_extracted = ? WHERE id = ?",
                    (json.dumps(course_skills), course_dict['id'])
                )
                
                all_skill_sources.append({
                    'source': 'course',
                    'source_id': course_dict['id'],
                    'skills': course_skill_data
                })
        
        # 3. Extract from Projects (including newly extracted ones)
        cursor.execute("SELECT * FROM projects WHERE user_id = ?", (user_id,))
        projects = cursor.fetchall()
        
        print(f"🚀 Processing {len(projects)} projects...")
        for project in projects:
            project_dict = dict(project)
            
            # Combine all project text
            text = f"{project_dict.get('project_name', '')} {project_dict.get('description', '')}"
            
            # Also include tech stack
            tech_stack = project_dict.get('tech_stack')
            if tech_stack:
                if isinstance(tech_stack, str):
                    tech_stack = json.loads(tech_stack)
                text += " " + " ".join(tech_stack)
            
            project_skills = skill_extractor.extract_skills_from_text(text)
            print(f"   Project '{project_dict.get('project_name', '')[:30]}...': {len(project_skills)} skills")
            
            project_skill_data = {}
            for skill in project_skills:
                prof, conf = skill_extractor.calculate_proficiency_from_project(skill, project_dict)
                project_skill_data[skill] = (prof, conf)
            
            if project_skill_data:
                # Update project with extracted skills
                cursor.execute(
                    "UPDATE projects SET skills_extracted = ? WHERE id = ?",
                    (json.dumps(project_skills), project_dict['id'])
                )
                
                all_skill_sources.append({
                    'source': 'project',
                    'source_id': project_dict['id'],
                    'skills': project_skill_data
                })
        
        # 4. Extract from Work Experience
        cursor.execute("SELECT * FROM work_experience WHERE user_id = ?", (user_id,))
        experiences = cursor.fetchall()
        
        print(f"💼 Processing {len(experiences)} work experiences...")
        for exp in experiences:
            exp_dict = dict(exp)
            text = f"{exp_dict.get('job_title', '')} {exp_dict.get('description', '')}"
            
            # Include technologies
            tech_used = exp_dict.get('technologies_used')
            if tech_used:
                if isinstance(tech_used, str):
                    tech_used = json.loads(tech_used)
                text += " " + " ".join(tech_used)
            
            exp_skills = skill_extractor.extract_skills_from_text(text)
            print(f"   Experience '{exp_dict.get('job_title', '')[:30]}...': {len(exp_skills)} skills")
            
            exp_skill_data = {}
            for skill in exp_skills:
                # Calculate proficiency based on experience data
                prof, conf = skill_extractor.calculate_proficiency_from_experience(skill, exp_dict)
                exp_skill_data[skill] = (prof, conf)
            
            if exp_skill_data:
                all_skill_sources.append({
                    'source': 'experience',
                    'source_id': exp_dict['id'],
                    'skills': exp_skill_data
                })
        
        # 5. Aggregate all skills
        print("🧠 Aggregating skills from all sources...")
        aggregated_skills = skill_extractor.aggregate_skills(all_skill_sources)
        
        # 6. Save to user_skills table
        print(f"💾 Saving {len(aggregated_skills)} skills to database...")
        
        # Clear existing skills
        cursor.execute("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
        
        # Insert new skills
        for skill_name, skill_data in aggregated_skills.items():
            cursor.execute('''
                INSERT INTO user_skills 
                (user_id, skill_name, proficiency, confidence, source_count, sources)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                skill_name,
                skill_data['proficiency'],
                skill_data['confidence'],
                skill_data['source_count'],
                json.dumps(skill_data['sources'])
            ))
        
        return {
            "message": "Skills extracted and resume data saved successfully",
            "user_id": user_id,
            "total_skills_extracted": len(aggregated_skills),
            "extracted_from_resume": extracted_data,
            "sources_processed": {
                "resume": 1 if resume_text else 0,
                "courses": len(courses),
                "projects": len(projects),
                "experience": len(experiences)
            },
            "skills": aggregated_skills
        }


# ===== LINKEDIN JOBS ENDPOINTS =====
@app.get("/api/jobs/search")
def search_jobs(
    title: str = "Healthcare Data Analyst",
    location: str = "United States",
    limit: int = 50
):
    """
    Search for jobs from LinkedIn.
    
    - **title**: Job title to search (e.g., "Healthcare Data Analyst")
    - **location**: Location filter (e.g., "United States", "India")
    - **limit**: Number of jobs to fetch (max: 100)
    """
    if not linkedin_fetcher:
        raise HTTPException(status_code=503, detail="LinkedIn API not configured. Set RAPIDAPI_KEY in .env")
    
    jobs_data = linkedin_fetcher.fetch_jobs(title, location, limit)
    
    return {
        "message": "Jobs fetched successfully",
        "total_jobs": jobs_data['total'],
        "cached": jobs_data.get('cached', False),
        "search_params": jobs_data.get('search_params', {}),
        "jobs": linkedin_fetcher.get_job_details(jobs_data)
    }


# ===== JOB SKILL ANALYSIS ENDPOINTS =====
@app.post("/api/jobs/analyze")
def analyze_job_skills(job_description: str):
    """
    Extract and analyze skills from a single job description.
    
    - **job_description**: Full job description text
    """
    if not job_description or len(job_description) < 50:
        raise HTTPException(status_code=400, detail="Job description too short")
    
    skills = job_analyzer.extract_skills_from_job(job_description)
    
    return {
        "message": "Job analyzed successfully",
        "required_skills": skills['required'],
        "preferred_skills": skills['preferred'],
        "total_skills": len(skills['all']),
        "all_skills": skills['all']
    }


@app.post("/api/jobs/market-analysis")
def analyze_market_requirements(
    title: str = "Healthcare Data Analyst",
    location: str = "United States",
    limit: int = 50
):
    """
    Fetch jobs and analyze market skill requirements.
    
    Returns aggregated skill requirements across all fetched jobs.
    """
    if not linkedin_fetcher:
        raise HTTPException(status_code=503, detail="LinkedIn API not configured. Set RAPIDAPI_KEY in .env")
    
    # Fetch jobs
    jobs_data = linkedin_fetcher.fetch_jobs(title, location, limit)
    jobs = linkedin_fetcher.get_job_details(jobs_data)
    
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found for analysis")
    
    # Analyze market requirements
    market_requirements = job_analyzer.aggregate_job_requirements(jobs)
    
    return {
        "message": "Market analysis complete",
        "jobs_analyzed": len(jobs),
        "search_params": {"title": title, "location": location},
        "market_requirements": market_requirements,
        "top_skills": list(market_requirements.keys())[:15]
    }


# ===== GAP ANALYSIS ENDPOINTS =====
@app.get("/api/users/{user_id}/gap-analysis")
def analyze_user_gaps(
    user_id: int,
    job_title: str = "Healthcare Data Analyst",
    location: str = "United States"
):
    """
    Perform comprehensive skill gap analysis for a user.
    
    Compares user's skills against market requirements.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user skills
        cursor.execute("SELECT * FROM user_skills WHERE user_id = ?", (user_id,))
        user_skills_rows = cursor.fetchall()
        
        if not user_skills_rows:
            raise HTTPException(status_code=400, detail="No skills found for user. Run skill extraction first.")
        
        # Format user skills
        user_skills = {}
        for row in user_skills_rows:
            skill_dict = dict(row)
            user_skills[skill_dict['skill_name']] = {
                'proficiency': skill_dict['proficiency'],
                'confidence': skill_dict['confidence']
            }
        
        # Get market requirements (from cache or API)
        if linkedin_fetcher:
            jobs_data = linkedin_fetcher.fetch_jobs(job_title, location, limit=50)
            jobs = linkedin_fetcher.get_job_details(jobs_data)
            market_requirements = job_analyzer.aggregate_job_requirements(jobs)
        else:
            # Use sample market data if API not available
            market_requirements = _get_sample_market_requirements()
        
        # Perform gap analysis
        gap_result = gap_analyzer.analyze_gaps(user_skills, market_requirements)
        
        return {
            "message": "Gap analysis complete",
            "user_id": user_id,
            "target_role": job_title,
            "user_skills_count": len(user_skills),
            "market_skills_count": len(market_requirements),
            "overall_readiness": gap_result['overall_readiness'],
            "summary": gap_result['summary'],
            "critical_gaps": gap_result['critical_gaps'][:5],
            "important_gaps": gap_result['important_gaps'][:5],
            "emerging_gaps": gap_result['emerging_gaps'][:5],
            "strengths": gap_result['strengths'][:5]
        }


def _get_sample_market_requirements() -> dict:
    """Return sample market requirements when API is unavailable."""
    return {
        "python": {"frequency": 0.85, "requirement_level": "critical", "avg_proficiency_needed": 0.75},
        "sql": {"frequency": 0.80, "requirement_level": "critical", "avg_proficiency_needed": 0.70},
        "machine-learning": {"frequency": 0.65, "requirement_level": "important", "avg_proficiency_needed": 0.65},
        "data-analysis": {"frequency": 0.75, "requirement_level": "critical", "avg_proficiency_needed": 0.70},
        "tensorflow": {"frequency": 0.45, "requirement_level": "important", "avg_proficiency_needed": 0.60},
        "healthcare-data": {"frequency": 0.55, "requirement_level": "important", "avg_proficiency_needed": 0.65},
        "nlp": {"frequency": 0.40, "requirement_level": "emerging", "avg_proficiency_needed": 0.55},
    }


# ===== COURSE RECOMMENDATION ENDPOINTS =====
@app.get("/api/users/{user_id}/recommended-courses")
def get_recommended_courses(
    user_id: int,
    max_courses_per_skill: int = 3
):
    """
    Get course recommendations based on user's skill gaps.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user skills
        cursor.execute("SELECT * FROM user_skills WHERE user_id = ?", (user_id,))
        user_skills_rows = cursor.fetchall()
        
        user_skills = {}
        for row in user_skills_rows:
            skill_dict = dict(row)
            user_skills[skill_dict['skill_name']] = {
                'proficiency': skill_dict['proficiency'],
                'confidence': skill_dict['confidence']
            }
        
        # Get market requirements
        market_requirements = _get_sample_market_requirements()
        
        # Perform gap analysis
        gap_result = gap_analyzer.analyze_gaps(user_skills, market_requirements)
        
        # Get skills to improve (critical + important gaps)
        skills_to_improve = [g['skill'] for g in gap_result['critical_gaps'][:3]]
        skills_to_improve += [g['skill'] for g in gap_result['important_gaps'][:2]]
        
        # Get course recommendations for each skill
        recommendations = []
        for skill in skills_to_improve:
            courses = course_recommender.search_courses_for_skill(skill, max_courses_per_skill)
            recommendations.append({
                'skill': skill,
                'gap_priority': 'critical' if skill in [g['skill'] for g in gap_result['critical_gaps']] else 'important',
                'courses': courses
            })
        
        return {
            "message": "Course recommendations generated",
            "user_id": user_id,
            "skills_targeted": len(skills_to_improve),
            "total_courses": sum(len(r['courses']) for r in recommendations),
            "recommendations": recommendations
        }


@app.get("/api/courses/search/{skill}")
def search_courses_for_skill(skill: str, max_results: int = 5):
    """
    Search for courses to learn a specific skill.
    """
    courses = course_recommender.search_courses_for_skill(skill, max_results)
    
    return {
        "skill": skill,
        "total_courses": len(courses),
        "courses": courses
    }


# ===== GITHUB ANALYSIS ENDPOINTS =====
@app.post("/api/users/{user_id}/analyze-github")
def analyze_user_github(user_id: int, github_url: Optional[str] = None):
    """
    Analyze user's GitHub profile to extract skills from repositories.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = dict(user)
        
        # Use provided URL or user's stored GitHub URL
        url = github_url or user_dict.get('github_url')
        
        if not url:
            raise HTTPException(status_code=400, detail="No GitHub URL provided. Pass github_url or update user profile.")
        
        # Analyze GitHub profile
        result = github_analyzer.analyze_github_profile(url, max_repos=10, fetch_readmes=True)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Save GitHub skills to database
        skills_saved = 0
        for skill, (proficiency, confidence) in result['skills_found'].items():
            # Check if skill already exists
            cursor.execute(
                "SELECT id, proficiency FROM user_skills WHERE user_id = ? AND skill_name = ?",
                (user_id, skill)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update if GitHub shows higher proficiency
                if proficiency > existing['proficiency']:
                    cursor.execute(
                        "UPDATE user_skills SET proficiency = ?, confidence = ?, sources = ? WHERE id = ?",
                        (proficiency, confidence, json.dumps(['github']), existing['id'])
                    )
                    skills_saved += 1
            else:
                # Insert new skill
                cursor.execute('''
                    INSERT INTO user_skills (user_id, skill_name, proficiency, confidence, source_count, sources)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, skill, proficiency, confidence, 1, json.dumps(['github'])))
                skills_saved += 1
        
        conn.commit()
        
        return {
            "message": "GitHub analysis complete",
            "user_id": user_id,
            "github_username": result['username'],
            "repos_analyzed": result['repos_analyzed'],
            "skills_found": len(result['skills_found']),
            "skills_saved": skills_saved,
            "skills": result['skills_found'],
            "repo_details": result['repo_details']
        }


# ===== COMPLETE ANALYSIS PIPELINE =====
@app.post("/api/users/{user_id}/complete-analysis")
def run_complete_analysis(
    user_id: int,
    target_job: str = "Healthcare Data Analyst",
    location: str = "United States"
):
    """
    Run complete skill intelligence pipeline:
    1. Extract skills from resume
    2. Analyze GitHub (if available)
    3. Fetch and analyze job market
    4. Perform gap analysis
    5. Generate course recommendations
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = dict(user)
        results = {"user_id": user_id, "stages": {}}
        
        # Stage 1: Extract skills from resume
        print("📄 Stage 1: Extracting skills from resume...")
        try:
            skill_result = extract_user_skills(user_id)
            results['stages']['skill_extraction'] = {
                "status": "success",
                "skills_extracted": skill_result['total_skills_extracted']
            }
        except Exception as e:
            results['stages']['skill_extraction'] = {"status": "failed", "error": str(e)}
        
        # Stage 2: Analyze GitHub (if URL available)
        print("🐙 Stage 2: Analyzing GitHub...")
        github_url = user_dict.get('github_url')
        if github_url:
            try:
                github_result = github_analyzer.analyze_github_profile(github_url, max_repos=5)
                results['stages']['github_analysis'] = {
                    "status": "success",
                    "repos_analyzed": github_result.get('repos_analyzed', 0),
                    "skills_found": len(github_result.get('skills_found', {}))
                }
            except Exception as e:
                results['stages']['github_analysis'] = {"status": "failed", "error": str(e)}
        else:
            results['stages']['github_analysis'] = {"status": "skipped", "reason": "No GitHub URL"}
        
        # Stage 3: Get market requirements
        print("📊 Stage 3: Analyzing job market...")
        if linkedin_fetcher:
            try:
                jobs_data = linkedin_fetcher.fetch_jobs(target_job, location, limit=30)
                jobs = linkedin_fetcher.get_job_details(jobs_data)
                market_requirements = job_analyzer.aggregate_job_requirements(jobs)
                results['stages']['market_analysis'] = {
                    "status": "success",
                    "jobs_analyzed": len(jobs),
                    "skills_identified": len(market_requirements)
                }
            except Exception as e:
                market_requirements = _get_sample_market_requirements()
                results['stages']['market_analysis'] = {"status": "fallback", "error": str(e)}
        else:
            market_requirements = _get_sample_market_requirements()
            results['stages']['market_analysis'] = {"status": "fallback", "reason": "API not configured"}
        
        # Stage 4: Gap analysis
        print("🔍 Stage 4: Performing gap analysis...")
        cursor.execute("SELECT * FROM user_skills WHERE user_id = ?", (user_id,))
        user_skills_rows = cursor.fetchall()
        
        user_skills = {}
        for row in user_skills_rows:
            skill_dict = dict(row)
            user_skills[skill_dict['skill_name']] = {
                'proficiency': skill_dict['proficiency'],
                'confidence': skill_dict['confidence']
            }
        
        gap_result = gap_analyzer.analyze_gaps(user_skills, market_requirements)
        results['stages']['gap_analysis'] = {
            "status": "success",
            "overall_readiness": gap_result['overall_readiness'],
            "critical_gaps": len(gap_result['critical_gaps']),
            "strengths": len(gap_result['strengths'])
        }
        
        # Stage 5: Course recommendations
        print("📚 Stage 5: Generating course recommendations...")
        skills_to_improve = [g['skill'] for g in gap_result['critical_gaps'][:3]]
        recommendations = []
        for skill in skills_to_improve:
            courses = course_recommender.search_courses_for_skill(skill, 2)
            recommendations.extend(courses)
        
        results['stages']['course_recommendations'] = {
            "status": "success",
            "skills_targeted": len(skills_to_improve),
            "courses_found": len(recommendations)
        }
        
        # Final summary
        results['summary'] = {
            "target_role": target_job,
            "overall_readiness": gap_result['overall_readiness'],
            "interpretation": gap_result['summary']['interpretation'],
            "top_priorities": gap_result['summary'].get('top_3_priorities', []),
            "user_skills": list(user_skills.keys()),
            "critical_gaps": [g['skill'] for g in gap_result['critical_gaps'][:5]],
            "recommended_courses": recommendations[:5]
        }
        
        return results


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Healthcare Skill Intelligence API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
