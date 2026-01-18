"""Analysis endpoints router - Gap Analysis, Course Recommendations, GitHub Analysis."""
import json
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.routers.dependencies import get_services, get_sample_market_requirements

router = APIRouter(prefix="/api", tags=["Analysis"])


# ===== GAP ANALYSIS ENDPOINTS =====
@router.get("/users/{user_id}/gap-analysis")
def analyze_user_gaps(
    user_id: int,
    job_title: str = "Healthcare Data Analyst",
    location: str = "United States"
):
    """
    Perform comprehensive skill gap analysis for a user.
    
    Compares user's skills against market requirements.
    """
    services = get_services()
    
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
            raise HTTPException(
                status_code=400, 
                detail="No skills found for user. Run skill extraction first."
            )
        
        # Format user skills
        user_skills = {}
        for row in user_skills_rows:
            skill_dict = dict(row)
            user_skills[skill_dict['skill_name']] = {
                'proficiency': skill_dict['proficiency'],
                'confidence': skill_dict['confidence']
            }
        
        # Get market requirements (from cache or API)
        if services.has_linkedin_api():
            linkedin_fetcher = services.linkedin_fetcher
            job_analyzer = services.job_analyzer
            
            jobs_data = linkedin_fetcher.fetch_jobs(job_title, location, limit=50)
            jobs = linkedin_fetcher.get_job_details(jobs_data)
            market_requirements = job_analyzer.aggregate_job_requirements(jobs)
        else:
            # Use sample market data if API not available
            market_requirements = get_sample_market_requirements()
        
        # Perform gap analysis
        gap_analyzer = services.gap_analyzer
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


# ===== COURSE RECOMMENDATION ENDPOINTS =====
@router.get("/users/{user_id}/recommended-courses")
def get_recommended_courses(
    user_id: int,
    max_courses_per_skill: int = 3
):
    """
    Get course recommendations based on user's skill gaps.
    """
    services = get_services()
    
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
        market_requirements = get_sample_market_requirements()
        
        # Perform gap analysis
        gap_analyzer = services.gap_analyzer
        course_recommender = services.course_recommender
        
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


@router.get("/courses/search/{skill}")
def search_courses_for_skill(skill: str, max_results: int = 5):
    """
    Search for courses to learn a specific skill.
    """
    services = get_services()
    course_recommender = services.course_recommender
    
    courses = course_recommender.search_courses_for_skill(skill, max_results)
    
    return {
        "skill": skill,
        "total_courses": len(courses),
        "courses": courses
    }


# ===== GITHUB ANALYSIS ENDPOINTS =====
@router.post("/users/{user_id}/analyze-github")
def analyze_user_github(user_id: int, github_url: Optional[str] = None):
    """
    Analyze user's GitHub profile to extract skills from repositories.
    """
    services = get_services()
    github_analyzer = services.github_analyzer
    
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
            raise HTTPException(
                status_code=400, 
                detail="No GitHub URL provided. Pass github_url or update user profile."
            )
        
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
@router.post("/users/{user_id}/complete-analysis")
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
    services = get_services()
    
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
            # Import here to avoid circular dependency
            from app.routers.skills import extract_user_skills
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
        github_analyzer = services.github_analyzer
        
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
        if services.has_linkedin_api():
            linkedin_fetcher = services.linkedin_fetcher
            job_analyzer = services.job_analyzer
            
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
                market_requirements = get_sample_market_requirements()
                results['stages']['market_analysis'] = {"status": "fallback", "error": str(e)}
        else:
            market_requirements = get_sample_market_requirements()
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
        
        gap_analyzer = services.gap_analyzer
        gap_result = gap_analyzer.analyze_gaps(user_skills, market_requirements)
        results['stages']['gap_analysis'] = {
            "status": "success",
            "overall_readiness": gap_result['overall_readiness'],
            "critical_gaps": len(gap_result['critical_gaps']),
            "strengths": len(gap_result['strengths'])
        }
        
        # Stage 5: Course recommendations
        print("📚 Stage 5: Generating course recommendations...")
        course_recommender = services.course_recommender
        
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
