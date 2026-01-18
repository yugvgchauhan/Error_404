"""Universal Resume Parser - Extract structured information from any resume format."""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class UniversalResumeParser:
    """Parse resume text to extract structured information - works with any format."""
    
    def __init__(self):
        # Comprehensive section patterns
        self.section_patterns = {
            'contact': r'\b(contact|contact\s+information|personal\s+details)\b',
            'summary': r'\b(summary|professional\s+summary|profile|objective|about\s+me)\b',
            'experience': r'\b(work\s+experience|professional\s+experience|experience|employment\s+history|work\s+history|career\s+history)\b',
            'education': r'\b(education|academic\s+background|qualifications|academic\s+qualifications)\b',
            'projects': r'\b(projects|personal\s+projects|academic\s+projects|portfolio)\b',
            'skills': r'\b(skills|technical\s+skills|core\s+competencies|expertise|technologies|proficiencies)\b',
            'certifications': r'\b(certificate|certifications|certificates|licenses|credentials)\b',
            'awards': r'\b(awards|honors|achievements|recognition|accomplishments)\b',
            'publications': r'\b(publications|research|papers|articles)\b',
            'volunteer': r'\b(volunteer|volunteering|community\s+service)\b',
            'languages': r'\b(languages|language\s+skills)\b',
            'interests': r'\b(interests|hobbies|personal\s+interests)\b',
        }
        
        # Flexible date patterns
        self.date_patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\s*[-–—to]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\s*[-–—to]\s*(present|current|now)',
            r'\d{1,2}/\d{4}\s*[-–—to]\s*\d{1,2}/\d{4}',
            r'\d{1,2}/\d{4}\s*[-–—to]\s*(present|current)',
            r'\b\d{4}\s*[-–—to]\s*\d{4}\b',
            r'\b\d{4}\s*[-–—to]\s*(present|current)\b',
        ]
        
        # Common technology keywords
        self.tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'sql', 'html', 'css',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'mongodb',
            'postgresql', 'mysql', 'aws', 'azure', 'docker', 'kubernetes', 'git', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'machine learning', 'deep learning', 'nlp', 'api'
        ]
        
        # Contact patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'[\+]?[(]?\d{1,4}[)]?[-\s\.]?\(?\d{1,4}\)?[-\s\.]?\d{1,4}[-\s\.]?\d{1,9}'
        self.url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    def extract_contact_info(self, text: str) -> Dict:
        """Extract contact information."""
        contact = {
            'email': re.search(self.email_pattern, text).group() if re.search(self.email_pattern, text) else '',
            'phone': '',
            'linkedin': '',
            'github': '',
            'location': ''
        }
        
        phone_match = re.search(self.phone_pattern, text)
        if phone_match:
            phone = phone_match.group()
            if len(re.sub(r'[\s\-\(\)\.]', '', phone)) >= 10:
                contact['phone'] = phone
        
        linkedin = re.search(r'linkedin\.com/in/[\w-]+', text, re.I)
        if linkedin:
            contact['linkedin'] = linkedin.group()
        
        github = re.search(r'github\.com/[\w-]+', text, re.I)
        if github:
            contact['github'] = github.group()
        
        return contact
    
    def extract_name(self, text: str) -> str:
        """Extract name from first few lines."""
        lines = [l.strip() for l in text.split('\n')[:5] if l.strip()]
        for line in lines:
            if not re.search(self.email_pattern, line) and not re.search(self.url_pattern, line):
                words = line.split()
                if 2 <= len(words) <= 4 and len(line) < 50:
                    if all(w[0].isupper() for w in words if w):
                        return line
        return lines[0] if lines else ""
    
    def split_into_sections(self, text: str) -> Dict[str, str]:
        """Split resume into sections."""
        sections = {}
        section_positions = []
        
        for section_type, pattern in self.section_patterns.items():
            for match in re.finditer(pattern, text, re.I):
                section_positions.append((match.start(), section_type))
        
        section_positions.sort()
        
        for i, (start, section_type) in enumerate(section_positions):
            end = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(text)
            sections[section_type] = text[start:end].strip()
        
        return sections
    
    def extract_dates(self, text: str) -> List[Tuple[str, str]]:
        """Extract date ranges."""
        dates = []
        for pattern in self.date_patterns:
            for match in re.finditer(pattern, text, re.I):
                parts = re.split(r'\s*[-–—]\s*|\s+to\s+', match.group(), flags=re.I)
                if len(parts) >= 2:
                    dates.append((parts[0].strip(), parts[1].strip()))
        return dates
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience."""
        if not text:
            return []
        
        experiences = []
        lines = text.split('\n')
        current = None
        desc_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            dates = self.extract_dates(line)
            is_bullet = line.startswith(('•', '-', '*', '>', '○'))
            
            if dates and not is_bullet:
                if current:
                    current['description'] = '\n'.join(desc_lines)
                    experiences.append(current)
                
                start, end = dates[0]
                line_clean = re.sub('|'.join(self.date_patterns), '', line, flags=re.I).strip('|-–— ')
                
                # Parse company/title
                if '|' in line_clean:
                    parts = line_clean.split('|')
                    title, company = parts[0].strip(), parts[1].strip()
                elif ' at ' in line_clean.lower():
                    parts = re.split(r'\s+at\s+', line_clean, flags=re.I)
                    title, company = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ''
                else:
                    title, company = line_clean, ''
                
                current = {
                    'company_name': company,
                    'job_title': title,
                    'start_date': start,
                    'end_date': end,
                    'description': '',
                    'technologies_used': [],
                    'employment_type': 'Full-time',
                    'location': ''
                }
                desc_lines = []
            
            elif current and is_bullet:
                bullet = line.lstrip('•-*>○ ')
                desc_lines.append(bullet)
                for tech in self.tech_keywords:
                    if tech in bullet.lower() and tech not in current['technologies_used']:
                        current['technologies_used'].append(tech)
        
        if current:
            current['description'] = '\n'.join(desc_lines)
            experiences.append(current)
        
        return experiences
    
    def extract_projects(self, text: str) -> List[Dict]:
        """Extract projects."""
        if not text:
            return []
        
        projects = []
        lines = text.split('\n')
        current = None
        desc_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            dates = self.extract_dates(line)
            is_bullet = line.startswith(('•', '-', '*', '>', '○'))
            
            if (dates and not is_bullet) or (not is_bullet and not current and 10 < len(line) < 100):
                if current:
                    current['description'] = '\n'.join(desc_lines)
                    projects.append(current)
                
                name = re.sub('|'.join(self.date_patterns), '', line, flags=re.I).strip('|-–— ')
                
                current = {
                    'project_name': name,
                    'description': '',
                    'tech_stack': [],
                    'github_link': '',
                    'deployed_link': '',
                    'role': 'Developer',
                    'project_type': 'Personal'
                }
                desc_lines = []
            
            elif current and is_bullet:
                bullet = line.lstrip('•-*>○ ')
                desc_lines.append(bullet)
                
                for tech in self.tech_keywords:
                    if tech in bullet.lower() and tech not in current['tech_stack']:
                        current['tech_stack'].append(tech)
                
                urls = re.findall(self.url_pattern, bullet)
                for url in urls:
                    if 'github' in url.lower():
                        current['github_link'] = url
                    else:
                        current['deployed_link'] = url
        
        if current:
            current['description'] = '\n'.join(desc_lines)
            projects.append(current)
        
        return projects
    
    def extract_education(self, text: str) -> List[Dict]:
        """Extract education."""
        if not text:
            return []
        
        education = []
        lines = text.split('\n')
        current = None
        
        degree_keywords = ['bachelor', 'master', 'phd', 'mba', 'b.s.', 'm.s.', 'b.tech', 'm.tech']
        
        for line in lines:
            line = line.strip()
            if len(line) < 5:
                continue
            
            has_degree = any(kw in line.lower() for kw in degree_keywords)
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            
            if has_degree or (year_match and not current):
                if current:
                    education.append(current)
                
                current = {
                    'degree': line if has_degree else '',
                    'university': '' if has_degree else line,
                    'graduation_year': int(year_match.group()) if year_match else None,
                    'gpa': ''
                }
                
                gpa_match = re.search(r'gpa[:\s]*(\d+\.?\d*)', line, re.I)
                if gpa_match:
                    current['gpa'] = gpa_match.group(1)
            
            elif current and not current.get('university'):
                current['university'] = line
        
        if current:
            education.append(current)
        
        return education
    
    def extract_certifications(self, text: str) -> List[Dict]:
        """Extract certifications."""
        if not text:
            return []
        
        certs = []
        lines = [l.strip().lstrip('•·-*>○ ') for l in text.split('\n') if l.strip()]
        
        for line in lines:
            if len(line) < 10:
                continue
            
            cert = {
                'certification_name': '', 
                'issuing_organization': '', 
                'issue_date': '',
                'credential_url': ''
            }
            
            date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b', line, re.I)
            if date_match:
                cert['issue_date'] = date_match.group()
                line = line.replace(date_match.group(), '')
            
            parts = re.split(r'\s*[-–—|,]\s*', line.strip())
            parts = [p.strip() for p in parts if p.strip()]
            
            if parts:
                cert['certification_name'] = parts[0]
                if len(parts) > 1:
                    cert['issuing_organization'] = parts[1]
                certs.append(cert)
        
        return certs
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills."""
        if not text:
            return []
        
        skills = set()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip().lstrip('•·-*>○ ')
            if not line:
                continue
            
            if ':' in line:
                line = line.split(':', 1)[1]
            
            for delimiter in [',', ';', '|']:
                if delimiter in line:
                    for item in line.split(delimiter):
                        skill = item.strip()
                        if 1 < len(skill) < 100:
                            skills.add(skill.lower())
                    break
            else:
                if 1 < len(line) < 100:
                    skills.add(line.lower())
        
        return list(skills)
    
    def parse_resume(self, text: str) -> Dict:
        """Parse entire resume."""
        sections = self.split_into_sections(text)
        
        return {
            'name': self.extract_name(text),
            'contact': self.extract_contact_info(text),
            'experience': self.extract_experience(sections.get('experience', '')),
            'education': self.extract_education(sections.get('education', '')),
            'projects': self.extract_projects(sections.get('projects', '')),
            'skills': self.extract_skills(sections.get('skills', '')),
            'certifications': self.extract_certifications(sections.get('certifications', '')),
            'summary': sections.get('summary', '').strip()[:500]
        }


# Example usage
if __name__ == "__main__":
    parser = UniversalResumeParser()
    
    sample = """
John Doe
john.doe@email.com | +1-234-567-8900 | linkedin.com/in/johndoe | github.com/johndoe
San Francisco, CA

PROFESSIONAL SUMMARY
Senior Software Engineer with 5+ years of experience in full-stack development

EXPERIENCE
Senior Software Engineer | Tech Corp
Jan 2020 - Present
• Developed microservices using Python and Django
• Led team of 5 developers in agile environment
• Built REST APIs serving 1M+ requests daily using FastAPI

Software Developer | StartupXYZ
Jun 2018 - Dec 2019
• Created React-based web applications
• Implemented CI/CD pipelines with Docker and Kubernetes

EDUCATION
Bachelor of Science in Computer Science
MIT | 2014-2018 | GPA: 3.8/4.0

PROJECTS
E-commerce Platform | Jan 2023 - Mar 2023
• Built using React, Node.js, and MongoDB
• Integrated Stripe payment gateway
• Deployed on AWS with auto-scaling
• GitHub: https://github.com/johndoe/ecommerce

SKILLS
Languages: Python, JavaScript, Java, SQL
Frameworks: React, Django, Flask, Node.js
Cloud: AWS, Docker, Kubernetes
Databases: PostgreSQL, MongoDB, Redis

CERTIFICATIONS
AWS Certified Solutions Architect - Amazon Web Services - Dec 2022
Certified Kubernetes Administrator - CNCF - Jan 2023
    """
    
    result = parser.parse_resume(sample)
    
    print("=== PARSED RESUME ===")
    print(f"\nName: {result['name']}")
    print(f"Email: {result['contact']['email']}")
    print(f"Phone: {result['contact']['phone']}")
    
    print(f"\n=== EXPERIENCE ({len(result['experience'])} entries) ===")
    for exp in result['experience']:
        print(f"• {exp['job_title']} at {exp['company_name']}")
        print(f"  {exp['start_date']} - {exp['end_date']}")
        print(f"  Tech: {', '.join(exp['technologies_used'][:5])}")
    
    print(f"\n=== EDUCATION ({len(result['education'])} entries) ===")
    for edu in result['education']:
        print(f"• {edu['degree']} - {edu['university']} ({edu['graduation_year']})")
    
    print(f"\n=== PROJECTS ({len(result['projects'])} entries) ===")
    for proj in result['projects']:
        print(f"• {proj['project_name']}")
        print(f"  Tech: {', '.join(proj['tech_stack'][:5])}")
    
    print(f"\n=== SKILLS ({len(result['skills'])} skills) ===")
    print(f"{', '.join(list(result['skills'])[:15])}")
    
    print(f"\n=== CERTIFICATIONS ({len(result['certifications'])} certs) ===")
    for cert in result['certifications']:
        print(f"• {cert['certification_name']} - {cert['issuing_organization']}")