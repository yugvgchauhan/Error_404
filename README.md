# 🏥 Healthcare Skill Intelligence System

An AI-powered skill gap analysis and course recommendation platform designed for healthcare professionals. The system extracts skills from resumes, analyzes job market requirements, identifies skill gaps, and recommends personalized learning paths.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Environment Variables](#-environment-variables)
- [How to Run](#-how-to-run)
- [API Endpoints](#-api-endpoints)
- [Test Credentials](#-test-credentials)
- [Error Handling](#-error-handling)
- [Example Usage](#-example-usage)
- [References](#-references)

---

## ✨ Features

### Core Features
- **👤 User Profile Management** - Register users with education, target roles, and career goals
- **📄 Resume Parsing** - Upload and parse PDF/DOCX resumes to extract skills automatically
- **🎯 Skill Extraction** - NLP-based extraction of technical and soft skills from any text
- **💼 LinkedIn Job Search** - Real-time job listings fetched via RapidAPI integration
- **📊 Job Skill Analysis** - Analyze job postings to identify required skills and trends
- **🔍 Gap Analysis** - Compare user skills with job requirements to identify gaps
- **📚 Course Recommendations** - AI-powered course suggestions via Tavily API to bridge skill gaps
- **🐙 GitHub Analysis** - Analyze GitHub repositories to extract demonstrated skills

### Additional Features
- **Course & Project Management** - Track completed courses and projects
- **Skill Proficiency Tracking** - Monitor skill levels (beginner/intermediate/expert)
- **Profile Completion Score** - Gamified profile completion tracking
- **RESTful API** - Fully documented with Swagger UI

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Backend Framework** | FastAPI |
| **Database** | SQLite with raw SQL queries |
| **Data Validation** | Pydantic v2 |
| **HTTP Client** | Requests, HTTPX |
| **NLP Processing** | spaCy, scikit-learn |
| **Document Parsing** | PyPDF2, python-docx |
| **External APIs** | Tavily API (courses), RapidAPI (LinkedIn jobs) |
| **API Documentation** | Swagger UI, ReDoc (built-in) |
| **Server** | Uvicorn (ASGI) |

---

## 📁 Project Structure

```
Error_404/
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create this)
├── healthcare_skills.db         # SQLite database (auto-created)
│
├── app/
│   ├── database.py              # Database connection & initialization
│   ├── models.py                # Data models
│   ├── schemas.py               # Pydantic request/response schemas
│   │
│   ├── routers/                 # API route modules
│   │   ├── __init__.py
│   │   ├── dependencies.py      # Shared services & DI container
│   │   ├── users.py             # User CRUD endpoints
│   │   ├── courses.py           # Course management
│   │   ├── projects.py          # Project management
│   │   ├── skills.py            # Skill extraction endpoints
│   │   ├── resume.py            # Resume upload & parsing
│   │   ├── jobs.py              # LinkedIn job search
│   │   └── analysis.py          # Gap analysis & recommendations
│   │
│   ├── services/                # Business logic services
│   │   ├── skill_extractor.py   # NLP skill extraction
│   │   ├── resume_parser.py     # PDF/DOCX parsing
│   │   ├── linkedin_job_fetcher.py  # LinkedIn API integration
│   │   ├── job_skill_analyzer.py    # Job posting analysis
│   │   ├── gap_analyzer.py      # Skill gap computation
│   │   ├── course_recommender.py    # Tavily course search
│   │   └── github_analyzer.py   # GitHub repo analysis
│   │
│   └── data/                    # Cache & data files
│       ├── cached_jobs/         # Cached job search results
│       ├── course_cache/        # Cached course recommendations
│       └── github_cache/        # Cached GitHub analysis
│
└── uploads/
    └── resumes/                 # Uploaded resume files
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/Error_404.git
cd Error_404
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Environment File
```bash
# Windows (PowerShell)
New-Item -Path .env -ItemType File

# macOS/Linux
touch .env
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required for LinkedIn Job Search
RAPIDAPI_KEY=your_rapidapi_key_here

# Required for Course Recommendations
TAVILY_API_KEY=your_tavily_api_key_here
```

### How to Get API Keys:

| API | Purpose | Get Key From |
|-----|---------|--------------|
| **RapidAPI** | LinkedIn job search | https://rapidapi.com/jaypat87/api/linkedin-jobs-search |
| **Tavily** | AI course search | https://tavily.com (Free tier available) |

> ⚠️ **Note**: The system works without API keys but with limited functionality:
> - Without `RAPIDAPI_KEY`: Job search returns cached/sample data
> - Without `TAVILY_API_KEY`: Course recommendations are limited

---

## ▶️ How to Run

### Start the Server
```bash
python main.py
```

**Output:**
```
🔑 RAPIDAPI_KEY loaded: Yes
🔑 TAVILY_API_KEY loaded: Yes
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Access the Application

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Health check endpoint |
| http://localhost:8000/docs | **Swagger UI** - Interactive API documentation |
| http://localhost:8000/redoc | ReDoc - Alternative API documentation |

### Run Tests
```bash
# Basic API test
python test_api.py

# Complete flow test
python test_complete_flow.py
```

---

## 📡 API Endpoints

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register` | Register a new user |
| GET | `/api/users` | List all users |
| GET | `/api/users/{user_id}` | Get user by ID |
| PUT | `/api/users/{user_id}` | Update user (partial update supported) |
| DELETE | `/api/users/{user_id}` | Delete user |
| GET | `/api/users/{user_id}/profile` | Get complete profile with stats |

### Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/{user_id}/courses` | Add a course |
| GET | `/api/users/{user_id}/courses` | List user's courses |
| PUT | `/api/users/{user_id}/courses/{course_id}` | Update course (partial) |
| DELETE | `/api/users/{user_id}/courses/{course_id}` | Delete course |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/{user_id}/projects` | Add a project |
| GET | `/api/users/{user_id}/projects` | List user's projects |
| PUT | `/api/users/{user_id}/projects/{project_id}` | Update project (partial) |
| DELETE | `/api/users/{user_id}/projects/{project_id}` | Delete project |

### Skills
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/skills/extract` | Extract skills from text |
| GET | `/api/users/{user_id}/skills` | Get user's extracted skills |

### Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/{user_id}/resume/upload` | Upload resume (PDF/DOCX/TXT) |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs/search` | Search LinkedIn jobs |
| POST | `/api/jobs/analyze` | Analyze job posting for skills |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/gap-analysis` | Perform skill gap analysis |
| POST | `/api/recommendations/courses` | Get course recommendations |
| POST | `/api/github/analyze` | Analyze GitHub profile |

---

## 🔑 Test Credentials

No authentication is required for the current version. You can test with any data.

### Sample Test User
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "education": "B.Tech Computer Science",
  "target_role": "Healthcare Data Analyst"
}
```

### Sample Test Flow
```bash
# 1. Register user → Returns user_id
# 2. Add courses/projects
# 3. Upload resume
# 4. Search jobs
# 5. Run gap analysis
# 6. Get course recommendations
```

---

## ⚠️ Error Handling

The API returns consistent error responses:

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid input data |
| `404` | Not Found | User/Course/Project not found |
| `422` | Validation Error | Missing required fields |
| `500` | Server Error | Internal server error |

### Error Response Format
```json
{
  "detail": "User not found"
}
```

### Validation Error Format
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Handling Errors in Code
```python
import requests

response = requests.post("http://localhost:8000/api/users/register", json=data)

if response.status_code == 201:
    user = response.json()
    print(f"User created: {user['id']}")
elif response.status_code == 400:
    print(f"Bad request: {response.json()['detail']}")
elif response.status_code == 422:
    errors = response.json()['detail']
    for error in errors:
        print(f"Validation error: {error['msg']}")
else:
    print(f"Error: {response.status_code}")
```

---

## 💡 Example Usage

### Complete Workflow Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register a new user
user_data = {
    "name": "Dr. Sarah Johnson",
    "email": "sarah.johnson@hospital.com",
    "education": "MD, MPH Public Health",
    "target_role": "Healthcare Data Scientist"
}
response = requests.post(f"{BASE_URL}/api/users/register", json=user_data)
user_id = response.json()["id"]
print(f"✅ User registered with ID: {user_id}")

# 2. Add a completed course
course_data = {
    "course_name": "Machine Learning for Healthcare",
    "platform": "Coursera",
    "instructor": "Stanford University",
    "description": "Applied ML techniques in healthcare settings"
}
requests.post(f"{BASE_URL}/api/users/{user_id}/courses", json=course_data)
print("✅ Course added")

# 3. Add a project
project_data = {
    "project_name": "Patient Readmission Predictor",
    "description": "ML model to predict hospital readmissions",
    "tech_stack": ["Python", "scikit-learn", "Pandas", "SQL"],
    "role": "Lead Developer"
}
requests.post(f"{BASE_URL}/api/users/{user_id}/projects", json=project_data)
print("✅ Project added")

# 4. Extract skills from text
skill_response = requests.post(f"{BASE_URL}/api/skills/extract", json={
    "text": "Experience with Python, SQL, machine learning, TensorFlow, and healthcare analytics"
})
skills = skill_response.json()
print(f"✅ Extracted skills: {skills['skills']}")

# 5. Search for jobs
jobs = requests.get(f"{BASE_URL}/api/jobs/search", params={
    "job_title": "Healthcare Data Scientist",
    "location": "United States"
}).json()
print(f"✅ Found {len(jobs.get('jobs', []))} jobs")

# 6. Run gap analysis
gap_analysis = requests.post(f"{BASE_URL}/api/gap-analysis", json={
    "user_skills": ["python", "sql", "machine learning"],
    "job_skills": ["python", "sql", "machine learning", "deep learning", "nlp", "spark"]
}).json()
print(f"✅ Gap analysis: {len(gap_analysis['missing_skills'])} missing skills")

# 7. Get course recommendations
recommendations = requests.post(f"{BASE_URL}/api/recommendations/courses", json={
    "skills": gap_analysis['missing_skills'][:3],
    "max_per_skill": 2
}).json()
print(f"✅ Got course recommendations")

# 8. Get complete profile
profile = requests.get(f"{BASE_URL}/api/users/{user_id}/profile").json()
print(f"✅ Profile completion: {profile['profile_completion']}%")
```

---

## 📚 References

1. **V. Raman and P. Nedungadi**, "Automated Skill Extraction from Job Postings and Resumes Using NLP Techniques," *IEEE Access*, vol. 9, pp. 54722-54733, 2021.
   - https://ieeexplore.ieee.org/document/9376955

2. **V. S. Dave et al.**, "A Recommender System for Job-Skill Matching Based on Skill Gap Analysis," *ACM RecSys Conference*, pp. 144-152, 2018.
   - https://dl.acm.org/doi/10.1145/3297280.3297625

3. **Y. Shi et al.**, "SkillRec: A Data-Driven Approach to Job Skill Recommendation for Career Transition," *arXiv preprint*, 2023.
   - https://arxiv.org/abs/2302.06655

4. **M. Langins and L. Borgermans**, "Healthcare Workforce Competency Mapping: A Systematic Review," *BMC Health Services Research*, vol. 21, no. 475, 2021.
   - https://bmchealthservres.biomedcentral.com/articles/10.1186/s12913-021-06574-8

5. **E. Colombo et al.**, "LinkedIn Job Postings Analysis for Real-Time Labor Market Intelligence," *International Journal of Information Management*, vol. 65, 2022.
   - https://www.sciencedirect.com/science/article/pii/S0268401222000627

---

## 📞 Support

- **API Documentation**: http://localhost:8000/docs
- **Issues**: Create an issue on GitHub

---

## 📄 License

This project is developed for educational purposes.

---

**Made with ❤️ by Team Error_404**
