"""Test complete flow: Fetch jobs -> Extract skills from descriptions."""
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path('.env'))

from app.services.linkedin_job_fetcher import LinkedInJobFetcher
from app.services.skill_extractor import SkillExtractor
from app.services.job_skill_analyzer import JobSkillAnalyzer

# Initialize services
api_key = os.getenv('RAPIDAPI_KEY', '').strip().strip('"')
fetcher = LinkedInJobFetcher(api_key)
skill_extractor = SkillExtractor()
job_analyzer = JobSkillAnalyzer(skill_extractor)

# Fetch jobs
print("📥 Fetching jobs from LinkedIn...")
jobs_data = fetcher.fetch_jobs('Data Scientist', 'India', limit=3, use_cache=False)
jobs = fetcher.get_job_details(jobs_data)

print(f"✅ Fetched {len(jobs)} jobs with descriptions\n")

# Extract skills from each job description
print("="*60)
print("SKILL EXTRACTION FROM JOB DESCRIPTIONS")
print("="*60)

all_skills = set()

for i, job in enumerate(jobs, 1):
    print(f"\n--- Job {i}: {job['title']} at {job['company']} ---")
    
    if job['description']:
        skills = job_analyzer.extract_skills_from_job(job['description'])
        
        print(f"Required Skills ({len(skills['required'])}): {list(skills['required'].keys())[:10]}")
        print(f"Preferred Skills ({len(skills['preferred'])}): {list(skills['preferred'].keys())[:5]}")
        
        all_skills.update(skills['all'].keys())
    else:
        print("No description available")

print("\n" + "="*60)
print(f"TOTAL UNIQUE SKILLS FOUND ACROSS {len(jobs)} JOBS: {len(all_skills)}")
print("="*60)
print(sorted(all_skills)[:30])
