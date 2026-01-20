"""Skills extraction endpoints router."""
import json
import os
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from app.database import get_db
from app import schemas
from app.routers.dependencies import get_services

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("/users/{user_id}", response_model=List[schemas.UserSkillResponse])
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


@router.post("/extract/{user_id}")
def extract_user_skills(user_id: int):
    """
    Extract skills from all user data sources (resume, courses, projects).
    Also parses resume structure to extract and save projects, experience, certifications.
    This is the core ML/NLP component!
    """
    services = get_services()
    skill_extractor = services.skill_extractor
    resume_parser = services.resume_parser
    
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
        used_llm = False  # Track if LLM was used
        courses = []
        projects = []
        experiences = []
        
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
            
            # Extract skills using LLM if available, otherwise fallback to NLP
            print("🔎 Extracting skills from resume...")
            
            if services.has_llm_api():
                print("🤖 Using LLM for skill extraction...")
                llm_extractor = services.llm_skill_extractor
                llm_skills = llm_extractor.extract_skills_with_proficiency(resume_text)
                
                resume_skill_data = {}
                for skill_info in llm_skills:
                    skill_name = skill_info['skill_name']
                    resume_skill_data[skill_name] = (skill_info['proficiency'], skill_info['confidence'])
                
                if resume_skill_data:
                    print(f"   ✅ LLM extracted {len(resume_skill_data)} skills")
                    used_llm = True  # Mark that LLM was used
                else:
                    print("   ⚠️ LLM returned 0 skills (likely error), falling back to NLP...")
                    used_llm = False
            else:
                print("📝 Using NLP-based skill extraction (no LLM API key)...")
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
        
        # Skip additional NLP extraction if LLM was used (LLM already extracted comprehensive skills)
        if used_llm:
            print("⏭️ Skipping additional NLP extraction (LLM mode)")
            courses = []
            projects = []
            experiences = []
        else:
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
        if not used_llm:
            cursor.execute("SELECT * FROM projects WHERE user_id = ?", (user_id,))
            projects = cursor.fetchall()
        
        print(f"🚀 Processing {len(projects)} projects...")
        for project in projects:
            project_dict = dict(project)
            
            # Combine all project text
            text = f"{project_dict.get('project_name', '')} {project_dict.get('description', '')}"
            
            # Also include tech stack
            # Also include tech stack
            tech_stack = project_dict.get('tech_stack')
            if tech_stack:
                if isinstance(tech_stack, str):
                    try:
                        tech_stack = json.loads(tech_stack)
                    except json.JSONDecodeError:
                        # Fallback for non-JSON strings
                        tech_stack = [s.strip() for s in tech_stack.split(',') if s.strip()]
                
                if isinstance(tech_stack, list):
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
        if not used_llm:
            cursor.execute("SELECT * FROM work_experience WHERE user_id = ?", (user_id,))
            experiences = cursor.fetchall()
        
        print(f"💼 Processing {len(experiences)} work experiences...")
        for exp in experiences:
            exp_dict = dict(exp)
            text = f"{exp_dict.get('job_title', '')} {exp_dict.get('description', '')}"
            
            # Include technologies
            # Include technologies
            tech_used = exp_dict.get('technologies_used')
            if tech_used:
                if isinstance(tech_used, str):
                    try:
                        tech_used = json.loads(tech_used)
                    except json.JSONDecodeError:
                        # Fallback for non-JSON strings
                        tech_used = [s.strip() for s in tech_used.split(',') if s.strip()]
                
                if isinstance(tech_used, list):
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


@router.delete("/users/{user_id}")
def clear_user_skills(user_id: int):
    """Clear all skills for a user (useful before re-extraction)."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete skills
        cursor.execute("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
        
        return {"message": "User skills cleared successfully", "user_id": user_id}
