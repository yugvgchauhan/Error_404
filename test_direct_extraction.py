"""Test direct skill extraction from resume."""
from PyPDF2 import PdfReader
from app.services.skill_extractor import SkillExtractor

# Extract resume text
reader = PdfReader('uploads/resumes/user_1_resume.pdf')
resume_text = ''.join([page.extract_text() for page in reader.pages])

# Initialize skill extractor
extractor = SkillExtractor('app/data/healthcare_skills.json')

# Extract skills directly from resume
skills = extractor.extract_skills_from_resume(resume_text)

print("=" * 80)
print(f"SKILLS EXTRACTED DIRECTLY FROM RESUME: {len(skills)}")
print("=" * 80)
for i, skill in enumerate(sorted(skills), 1):
    print(f"{i:2d}. {skill}")
