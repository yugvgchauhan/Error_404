"""Test resume parser to debug extraction issues."""
from PyPDF2 import PdfReader
from app.services.resume_parser import ResumeParser

# Extract resume text
reader = PdfReader('uploads/resumes/user_1_resume.pdf')
resume_text = ''.join([page.extract_text() for page in reader.pages])

print("=" * 80)
print("RESUME TEXT LENGTH:", len(resume_text))
print("=" * 80)

# Test parser
parser = ResumeParser()

# Split into sections
print("\n" + "=" * 80)
print("TESTING SECTION SPLITTING")
print("=" * 80)
sections = parser.split_into_sections(resume_text)
for section_name, section_text in sections.items():
    print(f"\n### {section_name.upper()} ###")
    print(f"Length: {len(section_text)} characters")
    print(f"Preview: {section_text[:200]}...")

# Parse full resume
print("\n" + "=" * 80)
print("TESTING FULL RESUME PARSING")
print("=" * 80)
parsed = parser.parse_resume(resume_text)

print(f"\n### EXPERIENCE ({len(parsed['experience'])} found) ###")
for exp in parsed['experience']:
    print(f"  - {exp['job_title']} at {exp['company_name']} ({exp['start_date']} - {exp['end_date']})")
    print(f"    Technologies: {exp['technologies_used']}")

print(f"\n### PROJECTS ({len(parsed['projects'])} found) ###")
for proj in parsed['projects']:
    print(f"  - {proj['project_name']}")
    print(f"    Tech stack: {proj['tech_stack']}")

print(f"\n### CERTIFICATIONS ({len(parsed['certifications'])} found) ###")
for cert in parsed['certifications']:
    print(f"  - {cert['certification_name']} from {cert['issuing_organization']}")

print(f"\n### SKILLS ({len(parsed['skills'])} found) ###")
print(f"  {', '.join(parsed['skills'][:20])}")

print("\n" + "=" * 80)
