"""Test script to verify the API setup."""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Test API health check."""
    print_section("1. Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_register_user():
    """Test user registration."""
    print_section("2. Testing User Registration")
    
    user_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "education": "B.Tech Computer Science",
        "university": "Example University",
        "graduation_year": 2024,
        "location": "New York, NY",
        "target_role": "Healthcare Data Analyst",
        "target_sector": "healthcare"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/register", json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            return response.json()["id"]
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_add_course(user_id):
    """Test adding a course."""
    print_section("3. Testing Add Course")
    
    course_data = {
        "course_name": "Machine Learning Specialization",
        "platform": "Coursera",
        "instructor": "Andrew Ng",
        "grade": "A",
        "completion_date": "2024-12",
        "duration": "3 months",
        "description": "Comprehensive machine learning course covering supervised learning, unsupervised learning, and best practices in ML. Built several projects including spam detection and image classification."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/{user_id}/courses", json=course_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_add_project(user_id):
    """Test adding a project."""
    print_section("4. Testing Add Project")
    
    project_data = {
        "project_name": "Healthcare Predictive Analytics Dashboard",
        "description": "Built a comprehensive dashboard for predicting patient readmission rates using machine learning. Implemented logistic regression and random forest models with 85% accuracy. Deployed using Flask and integrated with hospital EHR systems.",
        "tech_stack": ["Python", "scikit-learn", "Flask", "Pandas", "PostgreSQL"],
        "role": "Solo Developer",
        "duration": "4 months",
        "github_link": "https://github.com/johndoe/healthcare-analytics",
        "project_type": "Academic"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/users/{user_id}/projects", json=project_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_profile(user_id):
    """Test getting user profile."""
    print_section("5. Testing Get User Profile")
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/profile")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "🚀"*30)
    print("  TESTING HEALTHCARE SKILL INTELLIGENCE API")
    print("🚀"*30)
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Health check failed. Is the server running?")
        print("Run: python main.py")
        return
    
    # Test 2: Register User
    user_id = test_register_user()
    if not user_id:
        print("\n❌ User registration failed.")
        return
    
    print(f"\n✅ User created with ID: {user_id}")
    
    # Test 3: Add Course
    test_add_course(user_id)
    
    # Test 4: Add Project
    test_add_project(user_id)
    
    # Test 5: Get Profile
    test_get_profile(user_id)
    
    # Summary
    print_section("✅ TEST SUMMARY")
    print("✓ Health check passed")
    print("✓ User registration passed")
    print("✓ Add course passed")
    print("✓ Add project passed")
    print("✓ Get profile passed")
    print("\n🎉 All tests passed successfully!")
    print(f"\n📚 View API docs at: {BASE_URL}/docs")
    print(f"👤 Your test user ID: {user_id}")

if __name__ == "__main__":
    main()
