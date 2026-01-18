"""LLM-based skill extraction using Google Gemini."""
import os
import json
import re
from typing import List, Dict, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Import PDF/DOCX readers
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class LLMSkillExtractor:
    """Extract skills from resume using Google Gemini LLM."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model = None
        
        if not self.api_key:
            print("⚠️ Warning: No GEMINI_API_KEY found. LLM extraction will not work.")
            return
            
        if not GEMINI_AVAILABLE:
            print("⚠️ Warning: google-generativeai not installed. Run: pip install google-generativeai")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("✅ Gemini LLM initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if LLM extraction is available."""
        return self.model is not None
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT file."""
        if not os.path.exists(file_path):
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.pdf' and PdfReader:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            
            elif ext in ['.docx', '.doc'] and Document:
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            else:
                return ""
        except Exception as e:
            print(f"Error reading file: {e}")
            return ""
    
    def extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """
        Use Gemini to extract skills from resume text.
        Returns a list of skill names.
        """
        if not self.model:
            print("❌ LLM model not available")
            return []
        
        if not resume_text or len(resume_text.strip()) < 50:
            print("❌ Resume text too short")
            return []
        
        prompt = f"""You are an expert resume analyzer. Analyze the following resume and extract ALL technical skills, tools, technologies, programming languages, frameworks, and relevant professional skills.

IMPORTANT RULES:
1. Extract ONLY actual skills mentioned or clearly implied in the resume
2. Include programming languages (Python, Java, SQL, etc.)
3. Include frameworks and libraries (React, TensorFlow, Pandas, etc.)
4. Include tools and platforms (Git, Docker, AWS, etc.)
5. Include technical concepts (Machine Learning, Data Analysis, etc.)
6. Include relevant soft skills ONLY if explicitly mentioned (Leadership, Communication)
7. Do NOT make up skills that aren't in the resume
8. Return skills in lowercase with hyphens for multi-word skills (e.g., "machine-learning", "data-analysis")
9. Limit to the 15-25 most relevant and prominent skills

RESUME:
---
{resume_text[:8000]}
---

Return ONLY a JSON array of skill strings. Example format:
["python", "sql", "machine-learning", "react", "data-analysis", "tensorflow"]

JSON array of skills:"""

        try:
            print("🤖 Calling Gemini API for skill extraction...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response - extract JSON array
            # Try to find JSON array in response
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                skills_json = json_match.group(0)
                skills = json.loads(skills_json)
                
                # Clean and validate skills
                cleaned_skills = []
                for skill in skills:
                    if isinstance(skill, str):
                        # Normalize: lowercase, trim, replace spaces with hyphens
                        skill_clean = skill.strip().lower()
                        skill_clean = re.sub(r'\s+', '-', skill_clean)
                        if skill_clean and len(skill_clean) > 1:
                            cleaned_skills.append(skill_clean)
                
                print(f"✅ LLM extracted {len(cleaned_skills)} skills")
                return cleaned_skills
            else:
                print(f"❌ Could not parse JSON from response: {response_text[:200]}")
                return []
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return []
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return []
    
    def extract_skills_with_proficiency(self, resume_text: str) -> List[Dict]:
        """
        Extract skills with estimated proficiency levels.
        Returns list of {skill_name, proficiency, confidence}.
        """
        if not self.model:
            return []
        
        if not resume_text or len(resume_text.strip()) < 50:
            return []
        
        prompt = f"""You are an expert resume analyzer. Analyze the following resume and extract technical skills with proficiency estimates.

For each skill, estimate:
- proficiency: 0.0 to 1.0 (based on how much experience/depth is shown)
  - 0.3-0.5: Mentioned but little evidence of use
  - 0.5-0.7: Clear evidence of practical use
  - 0.7-0.85: Significant experience shown
  - 0.85-0.95: Expert level with projects/achievements
- confidence: 0.5 to 0.9 (how confident you are in this assessment)

RESUME:
---
{resume_text[:8000]}
---

Return ONLY a JSON array of objects. Example:
[
  {{"skill": "python", "proficiency": 0.8, "confidence": 0.85}},
  {{"skill": "machine-learning", "proficiency": 0.7, "confidence": 0.75}}
]

JSON array:"""

        try:
            print("🤖 Calling Gemini API for detailed skill extraction...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON array
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                skills_json = json_match.group(0)
                skills_data = json.loads(skills_json)
                
                # Validate and clean
                cleaned_skills = []
                for item in skills_data:
                    if isinstance(item, dict) and 'skill' in item:
                        skill_name = item['skill'].strip().lower()
                        skill_name = re.sub(r'\s+', '-', skill_name)
                        
                        proficiency = float(item.get('proficiency', 0.5))
                        confidence = float(item.get('confidence', 0.7))
                        
                        # Clamp values
                        proficiency = max(0.1, min(0.95, proficiency))
                        confidence = max(0.5, min(0.9, confidence))
                        
                        cleaned_skills.append({
                            'skill_name': skill_name,
                            'proficiency': proficiency,
                            'confidence': confidence
                        })
                
                print(f"✅ LLM extracted {len(cleaned_skills)} skills with proficiency")
                return cleaned_skills
            else:
                # Fallback to simple extraction
                simple_skills = self.extract_skills_from_resume(resume_text)
                return [
                    {'skill_name': s, 'proficiency': 0.6, 'confidence': 0.7}
                    for s in simple_skills
                ]
                
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return []
