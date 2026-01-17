"""FastAPI Healthcare Skill Intelligence System"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import os
from datetime import datetime

from app.database import get_db, init_db
from app import schemas
from app.services.skill_extractor import SkillExtractor

# Create uploads directory
UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize skill extractor
SKILLS_FILE = os.path.join("app", "data", "healthcare_skills.json")
skill_extractor = SkillExtractor(SKILLS_FILE)

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
            parsed_resume = skill_extractor.resume_parser.parse_resume(resume_text)
            
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
                prof, conf = skill_extractor.calculate_proficiency_from_resume(skill, resume_text)
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
                # Work experience gets high proficiency
                exp_skill_data[skill] = (0.80, 0.95)
            
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


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Healthcare Skill Intelligence API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
