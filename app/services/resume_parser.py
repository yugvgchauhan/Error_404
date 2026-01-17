"""Universal Resume parser to extract structured information from any resume format."""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ResumeParser:
    """Parse resume text to extract structured information - works with any resume format."""
    
    def __init__(self):
        # Multiple patterns for each section to handle various formats
        self.section_patterns = {
            'experience': [
                r'\b(work\s*experience|professional\s*experience|experience|employment(\s*history)?|work\s*history|career\s*history|positions?\s*held)\b',
            ],
            'education': [
                r'\b(education|academic(\s*background)?|qualifications?|educational\s*background|academic\s*qualifications?|degrees?)\b',
            ],
            'projects': [
                r'\b(projects?|personal\s*projects?|academic\s*projects?|side\s*projects?|portfolio|key\s*projects?)\b',
            ],
            'skills': [
                r'\b(skills?|technical\s*skills?|core\s*competenc(y|ies)|expertise|proficienc(y|ies)|technologies?|tools?|languages?\s*&?\s*(frameworks?)?)\b',
            ],
            'certifications': [
                r'\b(certificat(e|ion)s?|licenses?|credentials?|professional\s*certificat(e|ion)s?|accreditations?)\b',
            ],
            'summary': [
                r'\b(summary|profile|objective|about(\s*me)?|professional\s*summary|career\s*summary|executive\s*summary)\b',
            ],
        }
        
        # Date patterns - multiple formats
        self.date_patterns = [
            # Month/Year formats
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,.\s]+\d{4}',
            r'\d{1,2}/\d{4}',  # MM/YYYY
            r'\d{4}[-/]\d{1,2}',  # YYYY-MM
            r'\d{4}',  # Just year
        ]
        
        # Date range pattern
        self.date_range_pattern = r'({date})\s*[-–—to]+\s*({date}|present|current|now|ongoing)'
        
        # Common job titles
        self.job_title_keywords = [
            'engineer', 'developer', 'analyst', 'manager', 'director', 'lead', 'senior', 'junior',
            'intern', 'associate', 'consultant', 'specialist', 'architect', 'administrator',
            'scientist', 'designer', 'coordinator', 'executive', 'officer', 'head', 'chief',
            'vp', 'vice president', 'founder', 'co-founder', 'president', 'ceo', 'cto', 'cfo',
            'trainee', 'assistant', 'technician', 'supervisor', 'team lead'
        ]
    
    def _find_section_positions(self, text: str) -> List[Tuple[int, str, str]]:
        """Find all section headers and their positions in text."""
        positions = []
        text_lower = text.lower()
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
                    # Check if this looks like a section header (usually at start of line or after newline)
                    start = match.start()
                    # Look back for newline or start of text
                    line_start = text_lower.rfind('\n', 0, start)
                    if line_start == -1:
                        line_start = 0
                    else:
                        line_start += 1
                    
                    # Check if the match is near the start of the line (within first 50 chars)
                    if start - line_start < 50:
                        positions.append((start, section_type, match.group()))
        
        # Sort by position and remove duplicates (keep first occurrence of each type)
        positions.sort(key=lambda x: x[0])
        
        # Deduplicate by type, keeping earliest position
        seen_types = {}
        unique_positions = []
        for pos, section_type, header in positions:
            if section_type not in seen_types:
                seen_types[section_type] = True
                unique_positions.append((pos, section_type, header))
        
        return unique_positions
    
    def split_into_sections(self, text: str) -> Dict[str, str]:
        """Split resume text into sections."""
        sections = {}
        positions = self._find_section_positions(text)
        
        if not positions:
            # If no sections found, treat entire text as content
            return {'full_text': text}
        
        # Sort by position
        positions.sort(key=lambda x: x[0])
        
        for i, (start_pos, section_type, header) in enumerate(positions):
            # Get end position
            end_pos = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            
            # Extract section text
            section_text = text[start_pos:end_pos].strip()
            
            # Remove the header
            header_end = section_text.lower().find(header.lower()) + len(header)
            section_text = section_text[header_end:].strip()
            
            # Clean up leading colons, dashes, etc.
            section_text = re.sub(r'^[\s:•\-–—]+', '', section_text)
            
            sections[section_type] = section_text
        
        return sections
    
    def _extract_date_range(self, text: str) -> Tuple[str, str]:
        """Extract start and end dates from text."""
        # Build comprehensive date pattern
        date_pat = r'(?:' + '|'.join(self.date_patterns) + r')'
        range_pattern = rf'({date_pat})\s*[-–—to]+\s*({date_pat}|present|current|now|ongoing)'
        
        match = re.search(range_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Try to find single date
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(), ''
        
        return '', ''
    
    def _looks_like_job_title(self, text: str) -> bool:
        """Check if text looks like a job title."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.job_title_keywords)
    
    def _looks_like_company(self, text: str) -> bool:
        """Check if text looks like a company name."""
        # Companies often have indicators like Inc., Ltd., LLC, Corp., etc.
        company_indicators = ['inc', 'ltd', 'llc', 'corp', 'company', 'technologies', 'solutions', 
                              'services', 'labs', 'software', 'systems', 'group', 'international',
                              'consulting', 'private', 'limited', 'pvt']
        text_lower = text.lower()
        return any(ind in text_lower for ind in company_indicators)
    
    def extract_experience(self, experience_text: str) -> List[Dict]:
        """Extract work experience entries from any format."""
        if not experience_text:
            return []
        
        experiences = []
        
        # Strategy 1: Split by double newlines (common separator between entries)
        entries = re.split(r'\n\s*\n+', experience_text)
        # Filter out None and empty entries
        entries = [e for e in entries if e]
        
        # Strategy 2: If that doesn't work well, try splitting by date patterns
        if len(entries) <= 1:
            date_pat = r'(?:' + '|'.join(self.date_patterns) + r')'
            range_pattern = rf'{date_pat}\s*[-–—to]+\s*(?:{date_pat}|present|current|now|ongoing)'
            entries = re.split(rf'(?=.*{range_pattern})', experience_text, flags=re.IGNORECASE | re.MULTILINE)
            # Filter out None and empty entries
            entries = [e for e in entries if e]
        
        for entry in entries:
            if not entry:
                continue
            entry = entry.strip()
            if len(entry) < 20:  # Too short to be meaningful
                continue
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue
            
            exp = {
                'company_name': '',
                'job_title': '',
                'employment_type': 'Full-time',
                'start_date': '',
                'end_date': '',
                'location': '',
                'description': '',
                'technologies_used': []
            }
            
            # Extract dates
            start_date, end_date = self._extract_date_range(entry)
            exp['start_date'] = start_date
            exp['end_date'] = end_date
            
            # Detect if internship
            if 'intern' in entry.lower():
                exp['employment_type'] = 'Internship'
            elif 'contract' in entry.lower():
                exp['employment_type'] = 'Contract'
            elif 'freelance' in entry.lower() or 'consultant' in entry.lower():
                exp['employment_type'] = 'Freelance'
            elif 'part-time' in entry.lower() or 'part time' in entry.lower():
                exp['employment_type'] = 'Part-time'
            
            # Try to identify company and job title from first few lines
            for i, line in enumerate(lines[:4]):
                # Skip lines that are mostly dates
                if re.match(r'^[\d/\-–—\s\w]*$', line) and len(line) < 30:
                    continue
                
                # Remove date from line for analysis
                clean_line = re.sub(r'\s*[-–—]\s*(?:' + '|'.join(self.date_patterns) + r').*$', '', line, flags=re.IGNORECASE)
                clean_line = re.sub(r'^(?:' + '|'.join(self.date_patterns) + r')\s*[-–—]\s*', '', clean_line, flags=re.IGNORECASE)
                clean_line = clean_line.strip()
                
                if not clean_line:
                    continue
                
                # Heuristics to identify company vs job title
                if not exp['company_name'] and (self._looks_like_company(clean_line) or 
                    (i == 0 and not self._looks_like_job_title(clean_line))):
                    exp['company_name'] = clean_line
                elif not exp['job_title'] and (self._looks_like_job_title(clean_line) or 
                    (not exp['company_name'] and i == 0)):
                    exp['job_title'] = clean_line
                elif not exp['company_name']:
                    exp['company_name'] = clean_line
            
            # Extract bullet points as description
            bullet_lines = []
            for line in lines:
                if re.match(r'^[•·▪►◦‣⁃\-\*]\s*', line):
                    bullet_text = re.sub(r'^[•·▪►◦‣⁃\-\*]\s*', '', line)
                    bullet_lines.append(bullet_text)
                    
                    # Extract technologies
                    self._extract_technologies(bullet_text, exp['technologies_used'])
            
            exp['description'] = '\n'.join(bullet_lines)
            
            # Extract location (look for city, state patterns)
            location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*(?:[A-Z]{2}|[A-Z][a-z]+))\b'
            loc_match = re.search(location_pattern, entry)
            if loc_match:
                exp['location'] = loc_match.group(1)
            
            # Only add if we have meaningful content
            if exp['company_name'] or exp['job_title'] or exp['description']:
                experiences.append(exp)
        
        return experiences
    
    def _extract_technologies(self, text: str, tech_list: List[str]):
        """Extract technology keywords from text and add to list."""
        tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'sql', 'react', 'node', 'nodejs',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
            'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy', 'scikit-learn', 'sklearn',
            'flask', 'django', 'fastapi', 'spring', 'springboot', 'express',
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'git', 'github', 'gitlab', 'jira', 'confluence',
            'machine learning', 'ml', 'deep learning', 'dl', 'nlp', 'ai',
            'data analytics', 'data analysis', 'data science', 'big data',
            'streamlit', 'tableau', 'power bi', 'excel',
            'linux', 'unix', 'bash', 'shell',
            'html', 'css', 'bootstrap', 'tailwind',
            'rest', 'api', 'graphql', 'microservices',
            'agile', 'scrum', 'kanban',
            'c++', 'c#', 'go', 'rust', 'scala', 'kotlin', 'swift',
            'hadoop', 'spark', 'kafka', 'airflow',
            'opencv', 'yolo', 'bert', 'gpt', 'transformers',
            'langchain', 'llamaindex', 'rag', 'chromadb', 'pinecone',
        ]
        
        text_lower = text.lower()
        for tech in tech_keywords:
            if tech in text_lower and tech not in tech_list:
                tech_list.append(tech)
    
    def extract_projects(self, projects_text: str) -> List[Dict]:
        """Extract project entries from any format."""
        if not projects_text:
            return []
        
        projects = []
        
        # Split by double newlines or horizontal rules
        entries = re.split(r'\n\s*\n+|[-_=]{3,}', projects_text)
        # Filter out None and empty entries
        entries = [e for e in entries if e]
        
        for entry in entries:
            if not entry:
                continue
            entry = entry.strip()
            if len(entry) < 15:
                continue
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue
            
            project = {
                'project_name': '',
                'description': '',
                'tech_stack': [],
                'role': 'Developer',
                'github_link': '',
                'deployed_link': '',
                'project_type': 'Personal'
            }
            
            # First non-bullet line is likely the project name
            for i, line in enumerate(lines):
                if not re.match(r'^[•·▪►◦‣⁃\-\*]', line):
                    # Remove date if present
                    clean_name = re.sub(r'\s*[-–—|]\s*(?:' + '|'.join(self.date_patterns) + r').*$', '', line, flags=re.IGNORECASE)
                    clean_name = re.sub(r'^(?:' + '|'.join(self.date_patterns) + r')\s*[-–—|]\s*', '', clean_name, flags=re.IGNORECASE)
                    clean_name = clean_name.strip()
                    
                    if clean_name and len(clean_name) > 3:
                        project['project_name'] = clean_name
                        break
            
            # Extract bullet points as description
            bullet_lines = []
            for line in lines:
                if re.match(r'^[•·▪►◦‣⁃\-\*]\s*', line):
                    bullet_text = re.sub(r'^[•·▪►◦‣⁃\-\*]\s*', '', line)
                    bullet_lines.append(bullet_text)
                    
                    # Extract tech stack
                    self._extract_technologies(bullet_text, project['tech_stack'])
                    
                    # Extract URLs
                    urls = re.findall(r'https?://[^\s<>"]+', bullet_text)
                    for url in urls:
                        url = url.rstrip('.,;:)')
                        if 'github' in url.lower():
                            project['github_link'] = url
                        else:
                            project['deployed_link'] = url
            
            project['description'] = '\n'.join(bullet_lines)
            
            # Also extract tech from entire entry
            self._extract_technologies(entry, project['tech_stack'])
            
            # Detect project type
            entry_lower = entry.lower()
            if 'academic' in entry_lower or 'university' in entry_lower or 'college' in entry_lower:
                project['project_type'] = 'Academic'
            elif 'work' in entry_lower or 'company' in entry_lower or 'client' in entry_lower:
                project['project_type'] = 'Professional'
            elif 'hackathon' in entry_lower:
                project['project_type'] = 'Hackathon'
            
            # Detect role
            if 'lead' in entry_lower:
                project['role'] = 'Lead Developer'
            elif 'solo' in entry_lower or 'individual' in entry_lower:
                project['role'] = 'Solo Developer'
            elif 'team' in entry_lower:
                project['role'] = 'Team Member'
            
            if project['project_name'] or project['description']:
                projects.append(project)
        
        return projects
    
    def extract_certifications(self, cert_text: str) -> List[Dict]:
        """Extract certification entries from any format."""
        if not cert_text:
            return []
        
        certifications = []
        
        # Split by newlines, bullets, or numbers
        lines = re.split(r'\n|(?<=\.)(?=[A-Z])', cert_text)
        # Filter out None and empty lines
        lines = [l for l in lines if l]
        
        for line in lines:
            if not line:
                continue
            line = line.strip()
            line = re.sub(r'^[\d•·▪►◦‣⁃\-\*\.]+\s*', '', line)  # Remove bullets/numbers
            
            if len(line) < 10:
                continue
            
            cert = {
                'certification_name': '',
                'issuing_organization': '',
                'issue_date': '',
                'credential_url': ''
            }
            
            # Extract URL first
            url_match = re.search(r'https?://[^\s<>"]+', line)
            if url_match:
                cert['credential_url'] = url_match.group().rstrip('.,;:)')
                line = line.replace(url_match.group(), '').strip()
            
            # Extract date
            for pattern in self.date_patterns:
                date_match = re.search(pattern, line, re.IGNORECASE)
                if date_match:
                    cert['issue_date'] = date_match.group()
                    break
            
            # Split by common delimiters to separate name and issuer
            # Common patterns: "Cert Name - Issuer", "Cert Name | Issuer", "Cert Name, Issuer"
            parts = re.split(r'\s*[-–—|,]\s*', line, maxsplit=1)
            
            if parts:
                cert['certification_name'] = parts[0].strip()
                if len(parts) > 1:
                    # Remove date from issuer if present
                    issuer = parts[1]
                    for pattern in self.date_patterns:
                        issuer = re.sub(pattern, '', issuer, flags=re.IGNORECASE)
                    cert['issuing_organization'] = issuer.strip().strip('()[]')
            
            if cert['certification_name']:
                certifications.append(cert)
        
        return certifications
    
    def extract_education(self, edu_text: str) -> List[Dict]:
        """Extract education entries from any format."""
        if not edu_text:
            return []
        
        education = []
        
        # Split by double newlines
        entries = re.split(r'\n\s*\n+', edu_text)
        # Filter out None and empty entries
        entries = [e for e in entries if e]
        
        for entry in entries:
            if not entry:
                continue
            entry = entry.strip()
            if len(entry) < 15:
                continue
            
            edu = {
                'degree': '',
                'university': '',
                'graduation_year': None,
                'field': '',
                'gpa': ''
            }
            
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', entry)
            if year_match:
                edu['graduation_year'] = int(year_match.group())
            
            # Extract GPA
            gpa_match = re.search(r'(?:gpa|cgpa|grade)[:\s]*(\d+\.?\d*)[/\s]*(?:\d+\.?\d*)?', entry, re.IGNORECASE)
            if gpa_match:
                edu['gpa'] = gpa_match.group(1)
            
            # Common degree patterns
            degree_patterns = [
                r'\b(B\.?S\.?c?|M\.?S\.?c?|B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|Ph\.?D\.?|MBA|BBA|B\.?A\.?|M\.?A\.?|Bachelor|Master|Doctorate)\b[^,\n]*',
                r'\b(Bachelor|Master|Doctor)\s+of\s+[A-Za-z\s]+',
            ]
            
            for pattern in degree_patterns:
                degree_match = re.search(pattern, entry, re.IGNORECASE)
                if degree_match:
                    edu['degree'] = degree_match.group().strip()
                    break
            
            # University patterns - look for common indicators
            uni_indicators = ['university', 'college', 'institute', 'school', 'academy', 'iit', 'nit', 'bits', 'iiit']
            for line in lines:
                line_lower = line.lower()
                if any(ind in line_lower for ind in uni_indicators):
                    # Clean up the university name
                    uni_name = re.sub(r'\b(19|20)\d{2}\b', '', line)  # Remove year
                    uni_name = re.sub(r'[-–—|,]\s*.*$', '', uni_name)  # Remove trailing info
                    edu['university'] = uni_name.strip()
                    break
            
            # If no university found, use first line that's not the degree
            if not edu['university'] and lines:
                for line in lines:
                    if edu['degree'] and edu['degree'].lower() not in line.lower():
                        edu['university'] = line.split(',')[0].strip()
                        break
                    elif not edu['degree']:
                        edu['university'] = lines[0].split(',')[0].strip()
                        break
            
            # Extract field/major
            field_patterns = [
                r'(?:in|major(?:ing)?:?|specializ(?:ation|ing):?|field:?)\s+([A-Za-z\s&]+)',
                r'(?:Computer Science|Data Science|Information Technology|Software Engineering|Electrical Engineering|Mechanical Engineering|Business Administration)',
            ]
            
            for pattern in field_patterns:
                field_match = re.search(pattern, entry, re.IGNORECASE)
                if field_match:
                    edu['field'] = field_match.group(1).strip() if field_match.lastindex else field_match.group().strip()
                    break
            
            if edu['degree'] or edu['university']:
                education.append(edu)
        
        return education
    
    def extract_skills_section(self, skills_text: str) -> List[str]:
        """Extract skills from dedicated skills section."""
        if not skills_text:
            return []
        
        skills = set()
        
        # Handle various formats
        lines = skills_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullets and category labels
            line = re.sub(r'^[•·▪►◦‣⁃\-\*\d\.]+\s*', '', line)
            
            # Handle "Category: skill1, skill2, skill3" format
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    line = parts[1]
            
            # Split by various delimiters
            items = re.split(r'[,;|•·/]', line)
            
            for item in items:
                skill = item.strip()
                # Remove parenthetical info but note the skill
                skill = re.sub(r'\s*\([^)]*\)', '', skill)
                skill = skill.strip()
                
                if skill and 2 < len(skill) < 60:
                    # Normalize
                    skill_lower = skill.lower()
                    skills.add(skill_lower)
        
        return list(skills)
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume."""
        contact = {
            'email': '',
            'phone': '',
            'linkedin': '',
            'github': '',
            'website': '',
            'location': ''
        }
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone (various formats)
        phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            contact['phone'] = phone_match.group()
        
        # LinkedIn
        linkedin_match = re.search(r'(?:linkedin\.com/in/|linkedin:?\s*)([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        if linkedin_match:
            contact['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
        # GitHub
        github_match = re.search(r'(?:github\.com/|github:?\s*)([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        if github_match:
            contact['github'] = f"github.com/{github_match.group(1)}"
        
        # Website
        website_match = re.search(r'(?:website|portfolio|blog)[\s:]*([A-Za-z0-9.-]+\.[A-Za-z]{2,})', text, re.IGNORECASE)
        if website_match:
            contact['website'] = website_match.group(1)
        
        return contact
    
    def extract_name(self, text: str) -> str:
        """Try to extract name from resume (usually first line or prominent text)."""
        lines = text.strip().split('\n')
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Skip if too short or too long
            if len(line) < 3 or len(line) > 50:
                continue
            # Skip if contains email or phone
            if '@' in line or re.search(r'\d{3}[-.\s]?\d{3}', line):
                continue
            # Skip if looks like section header
            if any(header in line.lower() for header in ['experience', 'education', 'skills', 'summary', 'objective']):
                continue
            # Skip if contains URLs
            if 'http' in line.lower() or 'www.' in line.lower():
                continue
            
            # Likely a name if mostly letters and spaces, possibly with periods
            if re.match(r'^[A-Za-z\s.]+$', line):
                return line
        
        return ''
    
    def parse_resume(self, resume_text: str) -> Dict:
        """Parse entire resume and return structured data."""
        if not resume_text:
            return {}
        
        sections = self.split_into_sections(resume_text)
        
        parsed_data = {
            'name': self.extract_name(resume_text),
            'contact': self.extract_contact_info(resume_text),
            'experience': [],
            'projects': [],
            'certifications': [],
            'education': [],
            'skills': []
        }
        
        # Extract from each section
        if 'experience' in sections:
            parsed_data['experience'] = self.extract_experience(sections['experience'])
        
        if 'projects' in sections:
            parsed_data['projects'] = self.extract_projects(sections['projects'])
        
        if 'certifications' in sections:
            parsed_data['certifications'] = self.extract_certifications(sections['certifications'])
        
        if 'education' in sections:
            parsed_data['education'] = self.extract_education(sections['education'])
        
        if 'skills' in sections:
            parsed_data['skills'] = self.extract_skills_section(sections['skills'])
        
        # Also extract skills from experience and projects
        for exp in parsed_data['experience']:
            parsed_data['skills'].extend(exp.get('technologies_used', []))
        
        for proj in parsed_data['projects']:
            parsed_data['skills'].extend(proj.get('tech_stack', []))
        
        # Deduplicate skills
        parsed_data['skills'] = list(set(parsed_data['skills']))
        
        return parsed_data
