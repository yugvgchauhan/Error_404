# Healthcare Skill Intelligence System

AI-powered skill gap analysis platform for healthcare professionals.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python main.py
```

The API will be available at: http://localhost:8000

### 3. Test the API
```bash
python test_api.py
```

## 📚 API Documentation

Once the server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🎯 Available Endpoints

### User Management
- `POST /api/users/register` - Register a new user
- `GET /api/users/{user_id}` - Get user details
- `GET /api/users/{user_id}/profile` - Get complete profile with stats
- `GET /api/users` - List all users

### Courses
- `POST /api/users/{user_id}/courses` - Add a course
- `GET /api/users/{user_id}/courses` - Get all user courses

### Projects
- `POST /api/users/{user_id}/projects` - Add a project
- `GET /api/users/{user_id}/projects` - Get all user projects

### Skills
- `GET /api/users/{user_id}/skills` - Get extracted skills

## 📁 Project Structure

```
Error_404/
├── app/
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── data/
│       └── healthcare_skills.json  # Skills taxonomy
├── main.py                  # FastAPI application
├── api.py                   # LinkedIn API integration
├── test_api.py             # API test script
├── requirements.txt        # Python dependencies
└── healthcare_skills.db    # SQLite database (auto-created)
```

## 🔥 What's Working Now

✅ Database setup with SQLite
✅ User registration and profiles
✅ Course management
✅ Project management
✅ API documentation
✅ Test suite

## 🎯 Next Steps (Coming Soon)

- [ ] NLP Skill Extraction
- [ ] LinkedIn Job Fetching
- [ ] Gap Analysis Engine
- [ ] Course Recommendations
- [ ] Frontend Dashboard

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite + SQLAlchemy
- **Validation**: Pydantic
- **API Docs**: Swagger UI (built-in)

## 💡 Example Usage

```python
import requests

# Register a user
user_data = {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "education": "B.Tech Computer Science",
    "target_role": "Healthcare Data Analyst"
}
response = requests.post("http://localhost:8000/api/users/register", json=user_data)
user_id = response.json()["id"]

# Add a course
course_data = {
    "course_name": "Machine Learning",
    "platform": "Coursera",
    "description": "Comprehensive ML course..."
}
requests.post(f"http://localhost:8000/api/users/{user_id}/courses", json=course_data)

# Get profile
profile = requests.get(f"http://localhost:8000/api/users/{user_id}/profile").json()
print(f"Profile completion: {profile['profile_completion']}%")
```

## 📞 Support

For questions or issues, check the API documentation at `/docs`.
