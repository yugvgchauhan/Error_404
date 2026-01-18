"""Job search and analysis endpoints router."""
from fastapi import APIRouter, HTTPException

from app.routers.dependencies import get_services

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("/search")
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
    services = get_services()
    
    if not services.has_linkedin_api():
        raise HTTPException(
            status_code=503, 
            detail="LinkedIn API not configured. Set RAPIDAPI_KEY in .env"
        )
    
    linkedin_fetcher = services.linkedin_fetcher
    jobs_data = linkedin_fetcher.fetch_jobs(title, location, limit)
    
    return {
        "message": "Jobs fetched successfully",
        "total_jobs": jobs_data['total'],
        "cached": jobs_data.get('cached', False),
        "search_params": jobs_data.get('search_params', {}),
        "jobs": linkedin_fetcher.get_job_details(jobs_data)
    }


@router.post("/analyze")
def analyze_job_skills(job_description: str):
    """
    Extract and analyze skills from a single job description.
    
    - **job_description**: Full job description text
    """
    services = get_services()
    job_analyzer = services.job_analyzer
    
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


@router.post("/market-analysis")
def analyze_market_requirements(
    title: str = "Healthcare Data Analyst",
    location: str = "United States",
    limit: int = 50
):
    """
    Fetch jobs and analyze market skill requirements.
    
    Returns aggregated skill requirements across all fetched jobs.
    """
    services = get_services()
    
    if not services.has_linkedin_api():
        raise HTTPException(
            status_code=503, 
            detail="LinkedIn API not configured. Set RAPIDAPI_KEY in .env"
        )
    
    linkedin_fetcher = services.linkedin_fetcher
    job_analyzer = services.job_analyzer
    
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
