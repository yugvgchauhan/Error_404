# Healthcare Skill Intelligence API - Frontend Integration Guide

## Base URL
```
http://localhost:8000
```

## API Documentation
Interactive API docs available at: `http://localhost:8000/docs`

---

## 🎯 Core Workflow

1. **Register User** → 2. **Upload Resume** → 3. **Extract Skills** → 4. **Add Projects/Courses** → 5. **Gap Analysis** → 6. **Get Recommendations**

---

## 📋 API Endpoints Reference

### 1. USER MANAGEMENT (`/api/users`)

#### POST `/api/users/register` - Create New User
```json
Request:
{
  "name": "John Doe",
  "email": "john@example.com",
  "education": "Bachelor's in Computer Science",
  "university": "MIT",
  "graduation_year": 2020,
  "location": "New York",
  "target_role": "Data Analyst",
  "target_sector": "healthcare",
  "phone": "+1234567890",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe"
}

Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  ...all user fields
}
```

#### GET `/api/users/{user_id}` - Get User Details
```json
Response:
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "education": "Bachelor's in Computer Science",
  ...
}
```

#### GET `/api/users/{user_id}/profile` - Get Complete Profile
```json
Response:
{
  "user": {...user details...},
  "courses": [{...}, {...}],
  "projects": [{...}, {...}],
  "certifications": [{...}],
  "work_experience": [{...}],
  "skills": [{...}],
  "skill_count": 25,
  "course_count": 5,
  "project_count": 3
}
```

#### GET `/api/users` - List All Users
```json
Response: [
  {
    "id": 1,
    "name": "John Doe",
    ...
  }
]
```

#### PUT `/api/users/{user_id}` - Update User
```json
Request:
{
  "name": "John Smith",
  "target_role": "Senior Data Analyst"
}

Response: {updated user object}
```

#### DELETE `/api/users/{user_id}` - Delete User
```json
Response: {
  "message": "User deleted successfully"
}
```

---

### 2. RESUME MANAGEMENT (`/api/users/{user_id}/resume`)

#### POST `/api/users/{user_id}/resume/upload` - Upload Resume File
```
Request: multipart/form-data
- file: (PDF, DOCX, TXT file)

Response:
{
  "message": "Resume uploaded successfully",
  "user_id": 1,
  "filename": "user_1_resume.pdf",
  "file_path": "uploads/resumes/user_1_resume.pdf",
  "file_size": 45632
}
```

#### POST `/api/users/{user_id}/resume/upload-and-extract` - Upload Resume + Extract Skills
```
Request: multipart/form-data
- file: (PDF, DOCX, TXT file)

Response:
{
  "message": "Resume uploaded and skills extracted successfully",
  "user_id": 1,
  "filename": "user_1_resume.txt",
  "file_path": "uploads/resumes/user_1_resume.txt",
  "file_size": 892,
  "text_length": 850,
  "skills": ["Python", "Java", "React", "Docker", "AWS", ...],
  "skill_count": 27,
  "skills_saved_to_db": true
}
```

#### POST `/api/users/{user_id}/resume/upload-text` - Upload Resume as Text
```json
Request:
{
  "resume_text": "John Doe\nSoftware Engineer\n\nSkills: Python, React, AWS..."
}

Response:
{
  "message": "Resume text uploaded successfully",
  "user_id": 1,
  "filename": "user_1_resume.txt",
  "text_length": 850
}
```

#### GET `/api/users/{user_id}/resume/text` - Get Resume Text
```json
Response:
{
  "user_id": 1,
  "resume_text": "John Doe\nSoftware Engineer...",
  "source": "database"
}
```

#### GET `/api/users/{user_id}/resume/skills` - Get Extracted Skills from Database
```json
Response:
{
  "user_id": 1,
  "skills": [
    {
      "skill_name": "Python",
      "proficiency": 0.5,
      "confidence": 0.8,
      "source": "resume",
      "created_at": "2026-01-18T12:00:00"
    },
    ...
  ],
  "skill_count": 27,
  "source": "user_skills_table"
}
```

#### DELETE `/api/users/{user_id}/resume` - Delete Resume
```json
Response:
{
  "message": "Resume deleted successfully",
  "user_id": 1
}
```

---

### 3. SKILLS MANAGEMENT (`/api/skills`)

#### GET `/api/skills/users/{user_id}` - Get User Skills
```json
Response: [
  {
    "id": 1,
    "user_id": 1,
    "skill_name": "Python",
    "proficiency": 0.85,
    "confidence": 0.9,
    "source_count": 3,
    "sources": "resume,project,course",
    "last_updated": "2026-01-18T12:00:00"
  },
  ...
]
```

#### POST `/api/skills/extract/{user_id}` - Extract Skills from All Sources
```json
Response:
{
  "user_id": 1,
  "skills_extracted": 35,
  "skills": [
    {
      "skill_name": "Python",
      "proficiency": 0.85,
      "sources": ["resume", "project_1", "course_2"]
    },
    ...
  ],
  "message": "Skills extracted successfully"
}
```

#### DELETE `/api/skills/users/{user_id}` - Delete All User Skills
```json
Response:
{
  "message": "All skills deleted for user",
  "user_id": 1
}
```

---

### 4. PROJECTS MANAGEMENT (`/api/users/{user_id}/projects`)

#### POST `/api/users/{user_id}/projects` - Add Project
```json
Request:
{
  "project_name": "Healthcare Data Dashboard",
  "description": "Built a real-time healthcare analytics dashboard",
  "tech_stack": "React, Python, FastAPI, PostgreSQL",
  "role": "Full Stack Developer",
  "team_size": 4,
  "duration": "6 months",
  "github_link": "https://github.com/user/project",
  "deployed_link": "https://project.com",
  "project_type": "Web Application",
  "impact": "Reduced data analysis time by 50%"
}

Response:
{
  "id": 1,
  "user_id": 1,
  "project_name": "Healthcare Data Dashboard",
  ...all project fields,
  "created_at": "2026-01-18T12:00:00"
}
```

#### GET `/api/users/{user_id}/projects` - Get All User Projects
```json
Response: [
  {
    "id": 1,
    "project_name": "Healthcare Data Dashboard",
    ...
  }
]
```

#### GET `/api/users/{user_id}/projects/{project_id}` - Get Single Project
```json
Response: {project details}
```

#### PUT `/api/users/{user_id}/projects/{project_id}` - Update Project
```json
Request: {fields to update}
Response: {updated project}
```

#### DELETE `/api/users/{user_id}/projects/{project_id}` - Delete Project
```json
Response: {
  "message": "Project deleted successfully"
}
```

---

### 5. COURSES MANAGEMENT (`/api/users/{user_id}/courses`)

#### POST `/api/users/{user_id}/courses` - Add Course
```json
Request:
{
  "course_name": "Machine Learning Specialization",
  "platform": "Coursera",
  "instructor": "Andrew Ng",
  "grade": "A",
  "completion_date": "2023-12-15",
  "duration": "3 months",
  "description": "Comprehensive ML course covering supervised and unsupervised learning",
  "certificate_url": "https://coursera.org/certificate/xyz"
}

Response:
{
  "id": 1,
  "user_id": 1,
  "course_name": "Machine Learning Specialization",
  ...all course fields,
  "created_at": "2026-01-18T12:00:00"
}
```

#### GET `/api/users/{user_id}/courses` - Get All User Courses
```json
Response: [{course1}, {course2}, ...]
```

#### GET `/api/users/{user_id}/courses/{course_id}` - Get Single Course
```json
Response: {course details}
```

#### PUT `/api/users/{user_id}/courses/{course_id}` - Update Course
```json
Request: {fields to update}
Response: {updated course}
```

#### DELETE `/api/users/{user_id}/courses/{course_id}` - Delete Course
```json
Response: {
  "message": "Course deleted successfully"
}
```

---

### 6. JOBS & MARKET ANALYSIS (`/api/jobs`)

#### GET `/api/jobs/search?query=data+analyst&location=remote` - Search LinkedIn Jobs
```json
Query Parameters:
- query: "data analyst"
- location: "remote" (optional)

Response:
{
  "jobs": [
    {
      "title": "Senior Data Analyst",
      "company": "TechCorp",
      "location": "Remote",
      "description": "...",
      "skills_required": ["Python", "SQL", "Tableau"],
      "link": "https://linkedin.com/jobs/..."
    },
    ...
  ],
  "total": 10
}
```

#### POST `/api/jobs/analyze` - Analyze Job Skills Requirements
```json
Request:
{
  "job_description": "We are looking for a Data Analyst with Python, SQL, and Tableau experience..."
}

Response:
{
  "skills_extracted": ["Python", "SQL", "Tableau", "Excel", "R"],
  "skill_count": 5,
  "technical_skills": ["Python", "SQL", "Tableau"],
  "soft_skills": ["Communication", "Problem Solving"]
}
```

#### POST `/api/jobs/market-analysis` - Market Skills Analysis
```json
Request:
{
  "role": "Data Analyst",
  "location": "remote"
}

Response:
{
  "top_skills": [
    {"skill": "Python", "frequency": 85},
    {"skill": "SQL", "frequency": 78},
    {"skill": "Tableau", "frequency": 65}
  ],
  "total_jobs_analyzed": 50,
  "market_insights": "Python is the most demanded skill..."
}
```

---

### 7. ANALYSIS & RECOMMENDATIONS (`/api/analysis`)

#### GET `/api/analysis/users/{user_id}/gap-analysis` - Skill Gap Analysis
```json
Response:
{
  "user_id": 1,
  "user_skills": ["Python", "SQL", "React"],
  "market_skills": ["Python", "SQL", "Tableau", "Power BI", "R"],
  "gaps": [
    {
      "skill": "Tableau",
      "priority": "high",
      "demand": 85
    },
    {
      "skill": "Power BI",
      "priority": "high",
      "demand": 70
    }
  ],
  "matching_skills": ["Python", "SQL"],
  "match_percentage": 40,
  "recommendations": "Focus on learning Tableau and Power BI..."
}
```

#### GET `/api/analysis/users/{user_id}/recommended-courses` - Get Course Recommendations
```json
Response:
{
  "user_id": 1,
  "skill_gaps": ["Tableau", "Power BI", "R"],
  "recommended_courses": [
    {
      "skill": "Tableau",
      "courses": [
        {
          "title": "Tableau Fundamentals",
          "platform": "Udemy",
          "url": "https://...",
          "rating": 4.7,
          "duration": "10 hours"
        }
      ]
    }
  ],
  "total_recommendations": 15
}
```

#### GET `/api/analysis/courses/search/{skill}` - Search Courses by Skill
```json
Response:
{
  "skill": "Python",
  "courses": [
    {
      "title": "Python for Data Science",
      "platform": "Coursera",
      "instructor": "IBM",
      "url": "https://...",
      "rating": 4.8
    },
    ...
  ],
  "count": 10
}
```

#### POST `/api/analysis/users/{user_id}/analyze-github` - Analyze GitHub Profile
```json
Request:
{
  "github_username": "johndoe"
}

Response:
{
  "user_id": 1,
  "github_username": "johndoe",
  "repositories_analyzed": 15,
  "skills_extracted": ["Python", "JavaScript", "Docker", "React"],
  "top_languages": [
    {"language": "Python", "percentage": 45},
    {"language": "JavaScript", "percentage": 35}
  ],
  "projects": [
    {
      "name": "awesome-project",
      "description": "...",
      "languages": ["Python", "JavaScript"],
      "stars": 120
    }
  ]
}
```

#### POST `/api/analysis/users/{user_id}/complete-analysis` - Complete Skill Analysis
```json
Response:
{
  "user_id": 1,
  "profile_summary": {...},
  "all_skills": ["Python", "SQL", "React", ...],
  "skill_sources": {
    "resume": ["Python", "SQL"],
    "projects": ["React", "Docker"],
    "courses": ["Machine Learning"]
  },
  "gap_analysis": {...},
  "recommendations": [...],
  "github_analysis": {...},
  "completion_percentage": 85
}
```

---

## 📦 Data Models

### User
```typescript
{
  id: number
  name: string
  email: string
  education?: string
  university?: string
  graduation_year?: number
  location?: string
  target_role?: string
  target_sector: string (default: "healthcare")
  phone?: string
  linkedin_url?: string
  github_url?: string
  resume_path?: string
  resume_text?: string
  created_at: datetime
  updated_at: datetime
}
```

### Skill
```typescript
{
  id: number
  user_id: number
  skill_name: string
  proficiency: number (0.0-1.0)
  confidence: number (0.0-1.0)
  source_count: number
  sources: string (comma-separated)
  skill_metadata?: string (JSON)
  last_updated: datetime
  created_at: datetime
}
```

### Project
```typescript
{
  id: number
  user_id: number
  project_name: string
  description: string
  tech_stack?: string
  role?: string
  team_size?: number
  duration?: string
  github_link?: string
  deployed_link?: string
  project_type?: string
  impact?: string
  skills_extracted?: string (JSON)
  created_at: datetime
}
```

### Course
```typescript
{
  id: number
  user_id: number
  course_name: string
  platform?: string
  instructor?: string
  grade?: string
  completion_date?: string
  duration?: string
  description?: string
  certificate_url?: string
  skills_extracted?: string (JSON)
  created_at: datetime
}
```

---

## 🎨 Frontend Implementation Suggestions

### Key Pages to Build:

1. **Landing Page**
   - Hero section explaining the platform
   - Key features showcase
   - Call-to-action buttons

2. **User Registration / Profile Setup**
   - Form using POST `/api/users/register`
   - Fields: name, email, education, target role, etc.

3. **Resume Upload**
   - File upload component (PDF/DOCX/TXT)
   - Drag-and-drop interface
   - POST `/api/users/{user_id}/resume/upload-and-extract`
   - Display extracted skills immediately

4. **Dashboard / Profile Page**
   - GET `/api/users/{user_id}/profile`
   - Display user info, skills, projects, courses
   - Skill visualization (charts/graphs)
   - Profile completeness indicator

5. **Projects Management**
   - List view of projects
   - Add/Edit/Delete project forms
   - GitHub integration

6. **Courses Management**
   - List view of completed courses
   - Add/Edit/Delete course forms

7. **Skill Gap Analysis**
   - GET `/api/analysis/users/{user_id}/gap-analysis`
   - Visual comparison: Your Skills vs Market Requirements
   - Gap highlights with priority levels
   - Interactive charts (radar chart, bar chart)

8. **Course Recommendations**
   - GET `/api/analysis/users/{user_id}/recommended-courses`
   - Card-based layout for course suggestions
   - Filter by skill gap
   - Direct links to course platforms

9. **Job Search**
   - Search interface
   - GET `/api/jobs/search`
   - Job cards with skill matching
   - Save/bookmark functionality

10. **GitHub Analysis**
    - Input GitHub username
    - POST `/api/analysis/users/{user_id}/analyze-github`
    - Display repositories and extracted skills

### UI/UX Recommendations:

- **Color Scheme**: Healthcare-themed (blues, greens, whites)
- **Components**: 
  - Skill tags/badges
  - Progress bars for skill proficiency
  - File upload with preview
  - Loading states for API calls
  - Error handling with user-friendly messages
  - Success notifications

- **Navigation**: 
  - Sidebar/Top nav with: Dashboard, Resume, Projects, Courses, Analysis, Jobs
  
- **Responsive Design**: Mobile-first approach

### Tech Stack Suggestions:
- **Framework**: React, Next.js, or Vue.js
- **UI Library**: Tailwind CSS, Material-UI, Chakra UI, or shadcn/ui
- **State Management**: React Context, Redux, or Zustand
- **HTTP Client**: Axios or Fetch API
- **Charts**: Recharts, Chart.js, or D3.js
- **Forms**: React Hook Form or Formik

---

## 🔐 CORS Configuration

CORS is enabled for all origins in development:
```python
allow_origins=["*"]
```

For production, configure specific origins.

---

## ⚠️ Important Notes

1. **File Uploads**: Use `multipart/form-data` for resume uploads
2. **Error Handling**: All endpoints return standard HTTP status codes (200, 400, 404, 500)
3. **Date Format**: ISO 8601 format (YYYY-MM-DD)
4. **Skills Extraction**: Uses fallback pattern matching (spaCy unavailable on Python 3.14)
5. **Database**: SQLite3 at `healthcare_skills.db`

---

## 🚀 Quick Start Example

```javascript
// 1. Register User
const user = await fetch('http://localhost:8000/api/users/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'John Doe',
    email: 'john@example.com',
    target_role: 'Data Analyst'
  })
}).then(r => r.json())

// 2. Upload Resume
const formData = new FormData()
formData.append('file', resumeFile)
const resumeResult = await fetch(`http://localhost:8000/api/users/${user.id}/resume/upload-and-extract`, {
  method: 'POST',
  body: formData
}).then(r => r.json())

console.log('Extracted Skills:', resumeResult.skills)

// 3. Get Gap Analysis
const gapAnalysis = await fetch(`http://localhost:8000/api/analysis/users/${user.id}/gap-analysis`)
  .then(r => r.json())

console.log('Skill Gaps:', gapAnalysis.gaps)

// 4. Get Recommendations
const recommendations = await fetch(`http://localhost:8000/api/analysis/users/${user.id}/recommended-courses`)
  .then(r => r.json())

console.log('Recommended Courses:', recommendations.recommended_courses)
```

---

## 📞 Support

API Documentation: http://localhost:8000/docs
Server Port: 8000
Database: healthcare_skills.db (SQLite3)
