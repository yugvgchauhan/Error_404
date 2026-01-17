"""NLP-based skill extraction service."""
import re
import json
import os
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher
from collections import defaultdict
from .resume_parser import ResumeParser

# Import PDF/DOCX readers
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class SkillExtractor:
    """Extract skills from text using NLP techniques."""
    
    def __init__(self, skills_file_path: str):
        """Initialize with healthcare skills taxonomy."""
        with open(skills_file_path, 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
        
        self.skills_list = set(skills_data.get('skills', []))
        self.synonyms = skills_data.get('synonyms', {})
        self.categories = skills_data.get('categories', {})
        self.weights = skills_data.get('weights', {})
        self.resume_parser = ResumeParser()
        
        # Build reverse synonym map for quick lookup
        self.synonym_map = {}
        for canonical, variants in self.synonyms.items():
            for variant in variants:
                self.synonym_map[variant.lower()] = canonical
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces, hyphens, and alphanumeric
        text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_ngrams(self, text: str, max_n: int = 3) -> Set[str]:
        """Extract n-grams (unigrams, bigrams, trigrams) from text."""
        words = text.split()
        ngrams = set()
        
        for n in range(1, min(max_n + 1, len(words) + 1)):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                ngrams.add(ngram)
        
        return ngrams
    
    def fuzzy_match(self, text: str, skill: str, threshold: float = 0.88) -> bool:
        """Check if text contains skill with fuzzy matching."""
        text_lower = text.lower()
        skill_lower = skill.lower()
        
        # Exact match
        if skill_lower in text_lower:
            return True
        
        # Word boundary match for single words
        if '-' not in skill_lower and ' ' not in skill_lower:
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                return True
        
        # Fuzzy match using SequenceMatcher
        words = text_lower.split()
        skill_words = skill_lower.split('-')  # Handle hyphenated skills
        skill_words = [w for part in skill_words for w in part.split()]  # Further split
        
        # For single word skills
        if len(skill_words) == 1:
            for word in words:
                # Remove special characters for comparison
                clean_word = re.sub(r'[^\w]', '', word)
                clean_skill = re.sub(r'[^\w]', '', skill_words[0])
                ratio = SequenceMatcher(None, clean_word, clean_skill).ratio()
                if ratio >= threshold:
                    return True
        
        # For multi-word skills, check if appears as phrase
        for i in range(len(words) - len(skill_words) + 1):
            phrase = ' '.join(words[i:i+len(skill_words)])
            ratio = SequenceMatcher(None, phrase, ' '.join(skill_words)).ratio()
            if ratio >= threshold:
                return True
        
        return False
    
    def extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """Extract all skills directly from resume structure."""
        if not resume_text:
            return []
        
        all_skills = set()
        
        # Parse resume structure
        parsed = self.resume_parser.parse_resume(resume_text)
        
        # 1. Extract from dedicated SKILLS section
        if parsed.get('skills'):
            for skill in parsed['skills']:
                # Clean and normalize
                skill_clean = skill.strip().lower()
                if skill_clean and len(skill_clean) > 1:
                    all_skills.add(skill_clean)
        
        # 2. Extract technologies from projects
        if parsed.get('projects'):
            for project in parsed['projects']:
                for tech in project.get('tech_stack', []):
                    tech_clean = tech.strip().lower()
                    if tech_clean and len(tech_clean) > 1:
                        all_skills.add(tech_clean)
        
        # 3. Extract technologies from work experience
        if parsed.get('experience'):
            for exp in parsed['experience']:
                for tech in exp.get('technologies_used', []):
                    tech_clean = tech.strip().lower()
                    if tech_clean and len(tech_clean) > 1:
                        all_skills.add(tech_clean)
        
        return list(all_skills)
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using multiple techniques."""
        if not text:
            return []
        
        cleaned_text = self.clean_text(text)
        found_skills = set()
        
        # Extract n-grams
        ngrams = self.extract_ngrams(cleaned_text, max_n=4)
        
        # Match against skills taxonomy
        for skill in self.skills_list:
            skill_clean = skill.lower()
            
            # Check exact match in n-grams
            if skill_clean in ngrams:
                found_skills.add(skill)
                continue
            
            # Check synonym matches
            if skill_clean in self.synonym_map:
                canonical = self.synonym_map[skill_clean]
                if canonical in self.skills_list:
                    found_skills.add(canonical)
                    continue
            
            # Check if any synonym exists in text
            if skill in self.synonyms:
                for synonym in self.synonyms[skill]:
                    if synonym.lower() in cleaned_text:
                        found_skills.add(skill)
                        break
            
            # Fuzzy match for skills with hyphens or variations
            if self.fuzzy_match(cleaned_text, skill_clean, threshold=0.88):
                found_skills.add(skill)
        
        return list(found_skills)
    
    def calculate_proficiency_from_course(
        self,
        skill: str,
        course_data: Dict
    ) -> Tuple[float, float]:
        """
        Calculate skill proficiency from course data.
        Returns: (proficiency, confidence)
        """
        base_proficiency = 0.5  # Base for course completion
        confidence = 0.7
        
        # Grade boost
        grade = course_data.get('grade', '').upper()
        if grade in ['A+', 'A']:
            base_proficiency += 0.15
            confidence += 0.1
        elif grade in ['A-', 'B+']:
            base_proficiency += 0.10
        elif grade in ['B', 'B-']:
            base_proficiency += 0.05
        
        # Platform reputation boost
        platform = course_data.get('platform', '').lower()
        if platform in ['coursera', 'edx', 'mit', 'stanford']:
            base_proficiency += 0.05
            confidence += 0.05
        
        # Course level boost (check in name/description)
        text = f"{course_data.get('course_name', '')} {course_data.get('description', '')}".lower()
        if 'advanced' in text:
            base_proficiency += 0.10
        elif 'intermediate' in text:
            base_proficiency += 0.05
        
        # Cap at 0.70 (courses have theoretical limit)
        proficiency = min(base_proficiency, 0.70)
        confidence = min(confidence, 0.85)
        
        return (proficiency, confidence)
    
    def calculate_proficiency_from_project(
        self,
        skill: str,
        project_data: Dict
    ) -> Tuple[float, float]:
        """
        Calculate skill proficiency from project data.
        Returns: (proficiency, confidence)
        """
        base_proficiency = 0.60  # Base for hands-on project
        confidence = 0.75
        
        description = project_data.get('description', '').lower()
        
        # Complexity indicators
        complexity_terms = {
            'deployed': 0.15,
            'production': 0.15,
            'scalable': 0.10,
            'large-scale': 0.10,
            'complex': 0.10,
            'advanced': 0.10,
            'optimized': 0.08,
            'improved': 0.08,
            'integrated': 0.05,
            'api': 0.05
        }
        
        for term, boost in complexity_terms.items():
            if term in description:
                base_proficiency += boost
                confidence += 0.02
        
        # Team role boost
        role = project_data.get('role', '').lower()
        if 'lead' in role or 'architect' in role:
            base_proficiency += 0.10
            confidence += 0.05
        elif 'solo' in role:
            base_proficiency += 0.05
        
        # Duration boost
        duration = project_data.get('duration', '').lower()
        if any(term in duration for term in ['6 months', '7 months', '8 months', '9 months', '1 year', '2 year']):
            base_proficiency += 0.10
        elif any(term in duration for term in ['3 months', '4 months', '5 months']):
            base_proficiency += 0.05
        
        # Links boost (shows completion/quality)
        if project_data.get('github_link'):
            base_proficiency += 0.05
            confidence += 0.03
        if project_data.get('deployed_link'):
            base_proficiency += 0.10
            confidence += 0.05
        
        # Cap at 0.90 (projects can reach high proficiency)
        proficiency = min(base_proficiency, 0.90)
        confidence = min(confidence, 0.92)
        
        return (proficiency, confidence)
    
    def calculate_proficiency_from_resume(
        self,
        skill: str,
        resume_text: str
    ) -> Tuple[float, float]:
        """
        Calculate skill proficiency from resume mentions.
        Returns: (proficiency, confidence)
        """
        resume_lower = resume_text.lower()
        skill_lower = skill.lower()
        
        # Count mentions
        mention_count = resume_lower.count(skill_lower)
        
        # Check synonyms
        if skill in self.synonyms:
            for synonym in self.synonyms[skill]:
                mention_count += resume_lower.count(synonym.lower())
        
        # Base proficiency from mentions
        base_proficiency = 0.50
        if mention_count >= 5:
            base_proficiency = 0.75
        elif mention_count >= 3:
            base_proficiency = 0.65
        elif mention_count >= 2:
            base_proficiency = 0.55
        
        # Context boost (check for expertise indicators)
        expertise_terms = ['expert', 'proficient', 'advanced', 'extensive experience', 'strong', 'skilled']
        for term in expertise_terms:
            # Check if term appears near the skill (within 50 chars)
            pattern = f".{{0,50}}{re.escape(term)}.{{0,50}}{re.escape(skill_lower)}"
            if re.search(pattern, resume_lower):
                base_proficiency += 0.10
                break
        
        confidence = min(0.60 + (mention_count * 0.05), 0.80)
        proficiency = min(base_proficiency, 0.85)
        
        return (proficiency, confidence)
    
    def aggregate_skills(
        self,
        skill_sources: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Aggregate skills from multiple sources.
        
        Args:
            skill_sources: List of dicts with format:
                {
                    'source': 'course'|'project'|'resume',
                    'source_id': int,
                    'skills': {skill_name: (proficiency, confidence)}
                }
        
        Returns:
            Dict of {skill_name: {proficiency, confidence, source_count, sources}}
        """
        skill_data = defaultdict(lambda: {
            'proficiencies': [],
            'confidences': [],
            'sources': [],
            'source_types': []
        })
        
        # Collect all data
        for source_data in skill_sources:
            source_type = source_data['source']
            source_id = source_data.get('source_id', 0)
            
            for skill, (proficiency, confidence) in source_data['skills'].items():
                skill_data[skill]['proficiencies'].append(proficiency)
                skill_data[skill]['confidences'].append(confidence)
                skill_data[skill]['sources'].append(f"{source_type}:{source_id}")
                skill_data[skill]['source_types'].append(source_type)
        
        # Aggregate
        aggregated = {}
        for skill, data in skill_data.items():
            proficiencies = data['proficiencies']
            confidences = data['confidences']
            source_types = data['source_types']
            
            # Weighted average (give more weight to practical sources)
            source_weights = {
                'experience': 2.0,
                'project': 1.5,
                'certification': 1.2,
                'course': 1.0,
                'resume': 1.3
            }
            
            total_weight = sum(source_weights.get(st, 1.0) for st in source_types)
            weighted_prof = sum(
                p * source_weights.get(st, 1.0)
                for p, st in zip(proficiencies, source_types)
            ) / total_weight
            
            # Frequency boost
            source_count = len(proficiencies)
            frequency_boost = min(source_count * 0.05, 0.15)
            
            # Final proficiency
            final_proficiency = min(weighted_prof + frequency_boost, 1.0)
            
            # Confidence based on agreement
            avg_confidence = sum(confidences) / len(confidences)
            count_boost = min(source_count * 0.1, 0.2)
            final_confidence = min(avg_confidence + count_boost, 0.95)
            
            aggregated[skill] = {
                'proficiency': round(final_proficiency, 2),
                'confidence': round(final_confidence, 2),
                'source_count': source_count,
                'sources': data['sources']
            }
        
        return aggregated
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if not PdfReader:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
        
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        if not Document:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
        
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from file (PDF, DOCX, or TXT)."""
        if not os.path.exists(file_path):
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            return ""
