"""
Improved Pure Python Resume Skill Extractor
More accurate skill extraction with better filtering
Only extracts REAL skills, not random words
"""

import PyPDF2
import re
import json
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
from app.services.resume_parser import UniversalResumeParser


class SkillExtractor:
    """Extract ONLY actual skills from resume with improved accuracy"""
    
    def __init__(self, skills_file_path: str = None):
        # Comprehensive skill database - ONLY real tech/professional skills
        self.skill_patterns = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'php', 
                'ruby', 'go', 'golang', 'rust', 'kotlin', 'swift', 'scala', 'r', 
                'matlab', 'perl', 'shell', 'bash', 'powershell', 'c', 'objective-c',
                'dart', 'elixir', 'haskell', 'lua', 'julia', 'groovy', 'vba'
            ],
            'web_technologies': [
                'html', 'html5', 'css', 'css3', 'react', 'reactjs', 'angular', 
                'vue', 'vuejs', 'nodejs', 'node.js', 'express', 'django', 'flask', 
                'fastapi', 'rest', 'restful', 'rest api', 'graphql', 'bootstrap', 
                'tailwind', 'sass', 'scss', 'webpack', 'vite', 'redux', 'next.js',
                'nextjs', 'jquery', 'ajax', 'json', 'xml', 'websocket'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 
                'elasticsearch', 'oracle', 'cassandra', 'dynamodb', 'firebase', 
                'sqlite', 'mariadb', 'neo4j', 'couchdb', 'firestore'
            ],
            'cloud_platforms': [
                'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp', 
                'google cloud', 'heroku', 'digitalocean', 'docker', 'kubernetes', 
                'k8s', 's3', 'ec2', 'lambda', 'cloudflare', 'vercel', 'netlify'
            ],
            'devops_tools': [
                'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'git', 
                'ci/cd', 'terraform', 'ansible', 'chef', 'puppet', 'nginx', 
                'apache', 'circleci', 'travis ci', 'github actions', 'bitbucket'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch', 
                'keras', 'pandas', 'numpy', 'scikit-learn', 'sklearn', 'matplotlib', 
                'data analysis', 'nlp', 'natural language processing', 'computer vision', 
                'ai', 'artificial intelligence', 'data visualization', 'jupyter',
                'opencv', 'seaborn', 'plotly'
            ],
            'testing': [
                'selenium', 'pytest', 'junit', 'jest', 'cypress', 'postman', 
                'jmeter', 'cucumber', 'mocha', 'chai', 'testng'
            ],
            'project_management': [
                'agile', 'scrum', 'kanban', 'jira', 'confluence', 'trello', 
                'asana', 'waterfall', 'pmp', 'prince2', 'six sigma', 'lean'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 
                'critical thinking', 'time management', 'adaptability', 
                'collaboration', 'presentation', 'mentoring', 'coaching',
                'project management', 'analytical skills', 'decision making'
            ],
            'mobile_development': [
                'android', 'ios', 'react native', 'flutter', 'swift', 'swiftui',
                'kotlin', 'xamarin', 'ionic', 'cordova'
            ],
            'security': [
                'cybersecurity', 'penetration testing', 'ethical hacking', 
                'owasp', 'ssl', 'tls', 'oauth', 'jwt', 'encryption',
                'firewall', 'vpn'
            ],
            'design': [
                'ui design', 'ux design', 'ui/ux', 'figma', 'sketch', 
                'adobe xd', 'photoshop', 'illustrator', 'wireframing', 
                'prototyping', 'design thinking'
            ],
            'other_technologies': [
                'blockchain', 'ethereum', 'web3', 'iot', 'ar', 'vr',
                'game development', 'unity', 'unreal engine', 'linux', 
                'unix', 'windows', 'macos', 'api design', 'microservices'
            ]
        }
        
        # Words to EXCLUDE (not real skills)
        self.exclude_words = {
            'experience', 'years', 'developed', 'built', 'created', 'managed',
            'led', 'implemented', 'designed', 'worked', 'project', 'team',
            'company', 'role', 'position', 'responsible', 'duties', 'tasks',
            'strong', 'excellent', 'good', 'proficient', 'expert', 'beginner',
            'and', 'or', 'with', 'using', 'including', 'such', 'as', 'the',
            'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'from', 'by'
        }
        
        # Flatten all valid skills
        self.valid_skills = set()
        for category, skills in self.skill_patterns.items():
            for skill in skills:
                # Remove regex escapes for lookup
                clean_skill = skill.replace('\\+', '+').replace('\\#', '#').replace('\\.', '.')
                self.valid_skills.add(clean_skill.lower())

        # Initialize resume parser
        self.resume_parser = UniversalResumeParser()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"❌ Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            print(f"❌ Error reading TXT: {str(e)}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text based on file extension"""
        if file_path.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.txt'):
            return self.extract_text_from_txt(file_path)
        else:
            print("❌ Unsupported file format. Use PDF or TXT.")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def is_valid_skill(self, skill: str) -> bool:
        """Check if extracted term is a VALID skill"""
        skill_lower = skill.lower().strip()
        
        # Too short or too long
        if len(skill_lower) < 2 or len(skill_lower) > 50:
            return False
        
        # Check if in exclude list
        if skill_lower in self.exclude_words:
            return False
        
        # Check if it's a valid skill from our database
        if skill_lower in self.valid_skills:
            return True
        
        # Check for common patterns that indicate NOT a skill
        # Avoid complete sentences
        if len(skill_lower.split()) > 4:
            return False
        
        # Avoid words with too many numbers (like "5 years", "2020-2023")
        if re.search(r'\d{4}', skill_lower):  # Year patterns
            return False
        
        # Allow if it contains known tech indicators
        tech_indicators = ['.js', '.net', 'js', 'api', 'db', 'ml', 'ai', 'ui', 'ux']
        if any(indicator in skill_lower for indicator in tech_indicators):
            return True
        
        # Allow acronyms (2-5 uppercase letters)
        original = skill.strip()
        if re.match(r'^[A-Z]{2,5}$', original):
            return True
        
        return False
    
    def extract_skills_from_section(self, text: str) -> Set[str]:
        """Extract skills from dedicated skills section"""
        lines = text.split('\n')
        in_skills_section = False
        skills_content = []
        
        skill_headers = [
            'skills', 'technical skills', 'core competencies', 'expertise',
            'technologies', 'tools', 'programming languages', 'key skills'
        ]
        
        major_sections = [
            'experience', 'education', 'work history', 'employment',
            'projects', 'certifications', 'summary', 'objective'
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check for skills section header
            if any(header in line_lower for header in skill_headers):
                if len(line_lower) < 50:  # Likely a header, not content
                    in_skills_section = True
                    continue
            
            # Check if we've left skills section
            if in_skills_section:
                if any(section in line_lower for section in major_sections):
                    if len(line_lower) < 50:
                        break
                
                skills_content.append(line)
        
        # Parse skills from content
        skills_text = ' '.join(skills_content)
        extracted = set()
        
        # Split by delimiters
        for delimiter in [',', '•', '·', '|', ';', '\n', '/', '&']:
            parts = re.split(re.escape(delimiter), skills_text)
            for part in parts:
                skill = part.strip()
                
                # Clean up
                skill = re.sub(r'[^\w\s\-\+\#\.]', '', skill)
                skill = skill.strip()
                
                if self.is_valid_skill(skill):
                    extracted.add(skill.lower())
        
        return extracted
    
    def extract_skills_pattern_matching(self, text: str) -> Dict[str, Dict]:
        """Extract skills using pattern matching against known skills"""
        text_lower = self.clean_text(text)
        found_skills = {}
        
        for category, patterns in self.skill_patterns.items():
            for pattern in patterns:
                # Create regex pattern with word boundaries
                regex_pattern = r'\b' + re.escape(pattern) + r'\b'
                
                matches = list(re.finditer(regex_pattern, text_lower, re.IGNORECASE))
                
                if matches:
                    skill_name = pattern.replace('\\+', '+').replace('\\#', '#').replace('\\.', '.')
                    occurrences = len(matches)
                    
                    # Determine proficiency based on frequency
                    if occurrences >= 5:
                        proficiency = "expert"
                    elif occurrences >= 3:
                        proficiency = "advanced"
                    elif occurrences >= 2:
                        proficiency = "intermediate"
                    else:
                        proficiency = "beginner"
                    
                    # Get context
                    context = self.get_context(text, skill_name)
                    
                    if skill_name not in found_skills:
                        found_skills[skill_name] = {
                            'name': skill_name.title(),
                            'category': category.replace('_', ' ').title(),
                            'proficiency': proficiency,
                            'context': context,
                            'occurrences': occurrences,
                            'confidence': 0.95  # High confidence for pattern match
                        }
        
        return found_skills
    
    def get_context(self, text: str, skill: str, window: int = 60) -> str:
        """Get context around skill mention"""
        text_lower = text.lower()
        skill_lower = skill.lower()
        
        pos = text_lower.find(skill_lower)
        if pos == -1:
            return "Found in resume"
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(skill) + window)
        context = text[start:end].strip()
        
        # Clean up
        context = re.sub(r'\s+', ' ', context)
        if len(context) > 100:
            context = context[:97] + "..."
        
        return context
    
    def infer_skills_from_actions(self, text: str) -> Dict[str, Dict]:
        """Infer soft skills from action verbs"""
        text_lower = text.lower()
        inferred = {}
        
        action_patterns = {
            r'\b(led|managed|supervised|directed)\s+team': {
                'name': 'Leadership',
                'category': 'Soft Skills',
                'confidence': 0.85
            },
            r'\b(developed|built|created|designed|architected)\b': {
                'name': 'Software Development',
                'category': 'Technical',
                'confidence': 0.70
            },
            r'\b(analyzed|evaluated|assessed)\s+data': {
                'name': 'Data Analysis',
                'category': 'Technical',
                'confidence': 0.80
            },
            r'\b(presented|communicated|collaborated)\b': {
                'name': 'Communication',
                'category': 'Soft Skills',
                'confidence': 0.75
            }
        }
        
        for pattern, skill_info in action_patterns.items():
            if re.search(pattern, text_lower):
                skill_name = skill_info['name']
                inferred[skill_name.lower()] = {
                    'name': skill_name,
                    'category': skill_info['category'],
                    'proficiency': 'intermediate',
                    'context': 'Inferred from experience',
                    'occurrences': 1,
                    'confidence': skill_info['confidence']
                }
        
        return inferred
    
    def extract_skills(self, text: str) -> Dict:
        """Main extraction method - combines all techniques"""
        if not text or len(text.strip()) < 50:
            return {'skills': [], 'total_count': 0, 'by_category': {}}
        
        all_skills = {}
        
        # Method 1: Pattern matching (most reliable)
        pattern_skills = self.extract_skills_pattern_matching(text)
        all_skills.update(pattern_skills)
        
        # Method 2: Extract from skills section
        section_skills = self.extract_skills_from_section(text)
        for skill in section_skills:
            # Only add if it's a valid skill from our database
            if skill in self.valid_skills:
                if skill not in all_skills:
                    # Find the category
                    category = 'Other'
                    for cat, patterns in self.skill_patterns.items():
                        if skill in [p.replace('\\+', '+').replace('\\#', '#') for p in patterns]:
                            category = cat.replace('_', ' ').title()
                            break
                    
                    all_skills[skill] = {
                        'name': skill.title(),
                        'category': category,
                        'proficiency': 'intermediate',
                        'context': 'Listed in skills section',
                        'occurrences': 1,
                        'confidence': 0.90
                    }
        
        # Method 3: Infer soft skills from actions
        inferred_skills = self.infer_skills_from_actions(text)
        for skill_key, skill_data in inferred_skills.items():
            if skill_key not in all_skills:
                all_skills[skill_key] = skill_data
        
        # Convert to list format
        skills_list = list(all_skills.values())
        
        # Group by category
        by_category = defaultdict(list)
        for skill in skills_list:
            by_category[skill['category']].append(skill)
        
        return {
            'skills': skills_list,
            'total_count': len(skills_list),
            'by_category': dict(by_category)
        }
    
    def print_results(self, results: Dict):
        """Print results in a beautiful format"""
        skills = results['skills']
        
        if not skills:
            print("\n❌ No skills found in the resume.")
            return
        
        print("\n" + "="*80)
        print(f"{'✨ SKILLS EXTRACTED SUCCESSFULLY! ✨':^80}")
        print(f"{'Total Skills Found: ' + str(results['total_count']):^80}")
        print("="*80)
        
        by_category = results['by_category']
        
        for category, category_skills in sorted(by_category.items()):
            print(f"\n📌 {category.upper()} ({len(category_skills)} skills)")
            print("-" * 80)
            
            for skill in category_skills:
                prof_stars = {
                    'expert': '⭐⭐⭐⭐',
                    'advanced': '⭐⭐⭐',
                    'intermediate': '⭐⭐',
                    'beginner': '⭐'
                }
                
                print(f"\n  • {skill['name']}")
                print(f"    Level: {skill['proficiency'].upper()} {prof_stars.get(skill['proficiency'], '')}")
                print(f"    Found: {skill['occurrences']} time(s)")
                print(f"    Confidence: {int(skill['confidence']*100)}%")
                print(f"    Context: {skill['context']}")
        
        print("\n" + "="*80)
    
    def save_to_json(self, results: Dict, output_file: str = "skills_output.json"):
        """Save results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving JSON: {str(e)}")


    
    def extract_skills_from_resume(self, text: str) -> List[str]:
        """Extract skills from resume text."""
        result = self.extract_skills(text)
        return [s['name'].lower() for s in result['skills']]
        
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from any text."""
        result = self.extract_skills(text)
        return [s['name'].lower() for s in result['skills']]
    
    def calculate_proficiency_from_resume(self, skill: str, text: str) -> Tuple[float, float]:
        """Calculate proficiency from resume context."""
        occurrences = text.lower().count(skill.lower())
        proficiency = 0.5
        if occurrences > 4: proficiency = 0.9
        elif occurrences > 2: proficiency = 0.7
        return proficiency, 0.8

    def calculate_proficiency_from_course(self, skill: str, course: Dict) -> Tuple[float, float]:
        """Calculate proficiency from course data."""
        proficiency = 0.4
        grade = course.get('grade', '')
        if grade and grade.upper().startswith('A'):
            proficiency = 0.8
        elif grade and grade.upper().startswith('B'):
            proficiency = 0.7
        return proficiency, 0.8
        
    def calculate_proficiency_from_project(self, skill: str, project: Dict) -> Tuple[float, float]:
        """Calculate proficiency from project data."""
        return 0.6, 0.75

    def aggregate_skills(self, sources: List[Dict]) -> Dict:
        """Aggregate skills from multiple sources."""
        aggregated = {}
        for source in sources:
            for skill, (prof, conf) in source['skills'].items():
                if skill not in aggregated:
                    aggregated[skill] = {
                        'proficiency': prof,
                        'confidence': conf,
                        'sources': [source['source']],
                        'source_count': 1
                    }
                else:
                    curr = aggregated[skill]
                    curr['proficiency'] = (curr['proficiency'] + prof) / 2
                    curr['confidence'] = max(curr['confidence'], conf)
                    curr['sources'].append(source['source'])
                    curr['source_count'] += 1
        return aggregated


def main():
    """Main execution"""
    print("\n" + "="*80)
    print(f"{'🎯 RESUME SKILL EXTRACTOR':^80}")
    print(f"{'Accurate skill extraction with advanced filtering':^80}")
    print("="*80)
    
    file_path = input("\n📄 Enter resume file path (PDF or TXT): ").strip()
    
    if not file_path:
        print("❌ No file provided.")
        return
    
    # Clean path
    file_path = file_path.strip('"').strip("'")
    
    extractor = SkillExtractor()
    
    print("\n🔍 Extracting text...")
    text = extractor.extract_text_from_file(file_path)
    
    if not text:
        print("❌ Could not read file.")
        return
    
    print(f"✅ Extracted {len(text)} characters")
    print("🧠 Analyzing skills (this may take a moment)...")
    
    results = extractor.extract_skills(text)
    
    extractor.print_results(results)
    
    # Ask to save
    save = input("\n💾 Save results to JSON? (y/n): ").strip().lower()
    if save == 'y':
        filename = input("📝 Output filename (default: skills_output.json): ").strip()
        if not filename:
            filename = "skills_output.json"
        extractor.save_to_json(results, filename)
    
    print("\n✨ Done!\n")


if __name__ == "__main__":
    main()