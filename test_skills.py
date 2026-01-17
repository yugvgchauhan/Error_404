"""Test skill extraction from resume."""
from PyPDF2 import PdfReader
from app.services.skill_extractor import SkillExtractor

# Extract resume text
reader = PdfReader('uploads/resumes/user_1_resume.pdf')
resume_text = ''.join([page.extract_text() for page in reader.pages])

# Initialize skill extractor
extractor = SkillExtractor('app/data/healthcare_skills.json')

# Extract skills
skills = extractor.extract_skills_from_text(resume_text)

print("=" * 80)
print(f"SKILLS EXTRACTED: {len(skills)}")
print("=" * 80)
for i, skill in enumerate(sorted(skills), 1):
    print(f"{i:2d}. {skill}")

print("\n" + "=" * 80)
print("TESTING SPECIFIC SKILLS")
print("=" * 80)

test_skills = ['python', 'pandas', 'numpy', 'tensorflow', 'keras', 'nltk', 'spacy', 
               'scikit-learn', 'transformers', 'streamlit', 'flask', 'sql']

for skill in test_skills:
    found = skill in skills or any(s.lower() == skill.lower() for s in skills)
    status = "✓" if found else "✗"
    print(f"{status} {skill}")
