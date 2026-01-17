"""Add team data to the database via API."""
import requests
import json

BASE_URL = "http://localhost:8000"

# ===== EDIT YOUR TEAM DATA HERE =====

TEAM_DATA = [
    {
        "user": {
            "name": "Yug Chauhan",  # EDIT THIS
            "email": "yug@example.com",  # EDIT THIS
            "education": "B.Tech Computer Science",  # EDIT THIS
            "university": "Your University",  # EDIT THIS
            "graduation_year": 2026,  # EDIT THIS
            "location": "Ahmedabad, Gujarat, India",  # EDIT THIS
            "target_role": "Healthcare Data Analyst",  # EDIT THIS
            "phone": "+91 1234567890",  # EDIT THIS (optional)
            "linkedin_url": "https://linkedin.com/in/yug",  # EDIT THIS (optional)
            "github_url": "https://github.com/yug"  # EDIT THIS (optional)
        },
        "courses": [
            {
                "course_name": "Machine Learning Specialization",
                "platform": "Coursera",
                "instructor": "Andrew Ng",
                "grade": "A",
                "completion_date": "2024-12",
                "duration": "3 months",
                "description": "Comprehensive machine learning course covering supervised learning, unsupervised learning, neural networks, and best practices. Built multiple projects including spam detection, image classification, and recommendation systems using Python and TensorFlow."
            },
            {
                "course_name": "Healthcare Analytics",
                "platform": "edX",
                "instructor": "MIT",
                "grade": "A-",
                "completion_date": "2025-06",
                "duration": "6 weeks",
                "description": "Learned healthcare data analysis, EHR systems, patient data privacy (HIPAA), medical coding (ICD-10), and healthcare-specific machine learning applications. Used SQL and Python for analyzing clinical datasets."
            },
            {
                "course_name": "Data Visualization with Tableau",
                "platform": "Udemy",
                "grade": "Pass",
                "completion_date": "2025-10",
                "duration": "4 weeks",
                "description": "Created interactive dashboards for healthcare data visualization. Learned to connect to databases, create calculated fields, and design executive-level healthcare analytics dashboards showing patient outcomes and operational metrics."
            }
        ],
        "projects": [
            {
                "project_name": "Healthcare Predictive Analytics Dashboard",
                "description": "Built a comprehensive machine learning system to predict patient readmission rates for hospitals. Implemented logistic regression, random forest, and gradient boosting models achieving 87% accuracy. Created interactive Tableau dashboards showing risk scores, readmission trends, and cost analysis. Integrated with sample EHR data and deployed using Flask API. Project reduced predicted readmission rates by identifying high-risk patients for preventive care.",
                "tech_stack": ["Python", "scikit-learn", "Pandas", "Flask", "Tableau", "PostgreSQL", "SQL"],
                "role": "Team Lead",
                "team_size": 4,
                "duration": "4 months",
                "github_link": "https://github.com/yug/healthcare-analytics",
                "project_type": "Academic",
                "impact": "Achieved 87% accuracy in predicting readmissions, potentially reducing costs by 15%"
            },
            {
                "project_name": "Medical Image Classification using CNN",
                "description": "Developed a deep learning model using Convolutional Neural Networks to classify chest X-ray images for pneumonia detection. Used transfer learning with ResNet50 pre-trained model, achieving 92% accuracy. Preprocessed over 5000 medical images, implemented data augmentation, and created a web interface for doctors to upload and analyze X-rays. Followed HIPAA guidelines for patient data handling.",
                "tech_stack": ["Python", "TensorFlow", "Keras", "OpenCV", "Flask", "Docker"],
                "role": "Solo Developer",
                "duration": "3 months",
                "github_link": "https://github.com/yug/medical-imaging",
                "deployed_link": "https://medical-imaging-demo.herokuapp.com",
                "project_type": "Personal",
                "impact": "92% accuracy, processed 5000+ images, deployed for 50+ test users"
            }
        ]
    },
    {
        "user": {
            "name": "Team Member 2",  # EDIT THIS
            "email": "member2@example.com",  # EDIT THIS
            "education": "B.Tech Information Technology",  # EDIT THIS
            "university": "Your University",  # EDIT THIS
            "graduation_year": 2026,
            "location": "Mumbai, Maharashtra, India",
            "target_role": "Healthcare ML Engineer",
            "phone": "+91 9876543210",
            "linkedin_url": "https://linkedin.com/in/member2",
            "github_url": "https://github.com/member2"
        },
        "courses": [
            {
                "course_name": "Deep Learning Specialization",
                "platform": "Coursera",
                "instructor": "Andrew Ng",
                "grade": "A+",
                "completion_date": "2025-01",
                "duration": "4 months",
                "description": "Advanced deep learning covering CNNs, RNNs, LSTMs, transformers, and attention mechanisms. Built projects in computer vision and NLP. Implemented neural networks from scratch and used TensorFlow and PyTorch for healthcare image classification."
            },
            {
                "course_name": "SQL for Data Science",
                "platform": "Coursera",
                "grade": "A",
                "completion_date": "2024-08",
                "duration": "5 weeks",
                "description": "Mastered SQL queries, joins, subqueries, window functions, and database design. Worked with healthcare datasets including patient records, medication data, and clinical trials information. Optimized complex queries for performance."
            }
        ],
        "projects": [
            {
                "project_name": "Clinical NLP for Medical Records",
                "description": "Developed natural language processing system to extract medical entities (diseases, medications, symptoms) from unstructured clinical notes. Used spaCy and custom-trained NER models to identify and classify medical terms. Achieved 89% F1 score on medical entity extraction. Built API for integration with EHR systems.",
                "tech_stack": ["Python", "spaCy", "NLTK", "scikit-learn", "FastAPI", "MongoDB"],
                "role": "Solo Developer",
                "duration": "3 months",
                "github_link": "https://github.com/member2/clinical-nlp",
                "project_type": "Academic"
            }
        ]
    },
    {
        "user": {
            "name": "Team Member 3",  # EDIT THIS
            "email": "member3@example.com",  # EDIT THIS
            "education": "B.Tech Computer Engineering",
            "university": "Your University",
            "graduation_year": 2026,
            "location": "Pune, Maharashtra, India",
            "target_role": "Healthcare Data Scientist",
            "phone": "+91 5555555555"
        },
        "courses": [
            {
                "course_name": "Python for Data Science",
                "platform": "Coursera",
                "grade": "A",
                "completion_date": "2024-06",
                "duration": "8 weeks",
                "description": "Comprehensive Python programming for data analysis. Covered NumPy, Pandas, Matplotlib, Seaborn for data manipulation and visualization. Applied to healthcare datasets including patient demographics, clinical outcomes, and hospital operations data."
            },
            {
                "course_name": "Statistics for Data Science",
                "platform": "edX",
                "grade": "B+",
                "completion_date": "2024-11",
                "duration": "10 weeks",
                "description": "Statistical analysis methods including hypothesis testing, regression analysis, ANOVA, and probability distributions. Applied statistical methods to healthcare research data and clinical trial analysis."
            }
        ],
        "projects": [
            {
                "project_name": "Drug Discovery ML Pipeline",
                "description": "Built machine learning pipeline for predicting drug-protein interactions in pharmaceutical research. Used molecular fingerprints and deep learning to predict binding affinity. Processed chemical compound data from PubChem and protein sequences. Implemented random forest and neural network models achieving 84% accuracy.",
                "tech_stack": ["Python", "RDKit", "scikit-learn", "TensorFlow", "Pandas"],
                "role": "Contributor",
                "team_size": 3,
                "duration": "5 months",
                "project_type": "Academic"
            }
        ]
    },
    {
        "user": {
            "name": "Team Member 4",  # EDIT THIS
            "email": "member4@example.com",  # EDIT THIS
            "education": "B.Tech Electronics & Communication",
            "university": "Your University",
            "graduation_year": 2026,
            "location": "Delhi, India",
            "target_role": "Clinical Data Analyst"
        },
        "courses": [
            {
                "course_name": "Healthcare Data Analysis",
                "platform": "Udemy",
                "grade": "Pass",
                "completion_date": "2025-03",
                "duration": "6 weeks",
                "description": "Learned healthcare-specific data analysis techniques, working with EHR systems, understanding FHIR and HL7 standards, HIPAA compliance, and medical coding (ICD-10, CPT). Used Python and SQL for clinical data analysis."
            },
            {
                "course_name": "Data Analysis with Excel",
                "platform": "LinkedIn Learning",
                "grade": "Pass",
                "completion_date": "2024-09",
                "duration": "3 weeks",
                "description": "Advanced Excel skills including pivot tables, VLOOKUP, macros, and data visualization. Applied to healthcare operations data and patient outcome tracking."
            }
        ],
        "projects": [
            {
                "project_name": "Hospital Operations Dashboard",
                "description": "Created comprehensive Power BI dashboard for hospital operations management tracking patient flow, bed occupancy, wait times, and resource utilization. Connected to SQL database with real-time updates. Implemented KPIs for emergency department efficiency and patient satisfaction metrics.",
                "tech_stack": ["Power BI", "SQL Server", "DAX", "Python"],
                "role": "Solo Developer",
                "duration": "2 months",
                "github_link": "https://github.com/member4/hospital-ops",
                "project_type": "Internship"
            }
        ]
    }
]


def add_user_complete_data(user_data):
    """Add a user with all their courses and projects."""
    print(f"\n{'='*60}")
    print(f"Adding user: {user_data['user']['name']}")
    print('='*60)
    
    try:
        # 1. Register user
        print("📝 Registering user...")
        response = requests.post(f"{BASE_URL}/api/users/register", json=user_data['user'])
        response.raise_for_status()
        user = response.json()
        user_id = user['id']
        print(f"✅ User registered with ID: {user_id}")
        
        # 2. Add courses
        print(f"\n📚 Adding {len(user_data['courses'])} courses...")
        for i, course in enumerate(user_data['courses'], 1):
            response = requests.post(f"{BASE_URL}/api/users/{user_id}/courses", json=course)
            response.raise_for_status()
            print(f"  ✅ Course {i}: {course['course_name']}")
        
        # 3. Add projects
        print(f"\n🚀 Adding {len(user_data['projects'])} projects...")
        for i, project in enumerate(user_data['projects'], 1):
            response = requests.post(f"{BASE_URL}/api/users/{user_id}/projects", json=project)
            response.raise_for_status()
            print(f"  ✅ Project {i}: {project['project_name']}")
        
        # 4. Get profile summary
        print(f"\n📊 Getting profile summary...")
        response = requests.get(f"{BASE_URL}/api/users/{user_id}/profile")
        response.raise_for_status()
        profile = response.json()
        
        print(f"\n🎉 SUCCESS! Profile Summary:")
        print(f"  • Total Courses: {profile['total_courses']}")
        print(f"  • Total Projects: {profile['total_projects']}")
        print(f"  • Profile Completion: {profile['profile_completion']}%")
        
        return user_id
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def main():
    """Add all team members."""
    print("\n" + "🚀"*30)
    print("  ADDING TEAM DATA TO DATABASE")
    print("🚀"*30)
    
    print("\n⚠️  IMPORTANT: Make sure the server is running!")
    print("    Run: uv run uvicorn main:app --reload")
    print("    in another terminal before running this script.\n")
    
    input("Press Enter to continue...")
    
    # Test connection
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n✅ Server is running: {response.json()}")
    except:
        print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
        print("   Please start the server first!")
        return
    
    # Add all team members
    user_ids = []
    for i, user_data in enumerate(TEAM_DATA, 1):
        print(f"\n\n{'#'*60}")
        print(f"# TEAM MEMBER {i} of {len(TEAM_DATA)}")
        print('#'*60)
        
        user_id = add_user_complete_data(user_data)
        if user_id:
            user_ids.append(user_id)
    
    # Final summary
    print("\n\n" + "="*60)
    print("  🎉 ALL TEAM DATA ADDED SUCCESSFULLY!")
    print("="*60)
    print(f"\nTotal users added: {len(user_ids)}")
    print(f"User IDs: {user_ids}")
    
    print("\n📚 Next steps:")
    print("  1. Visit http://localhost:8000/docs to see all APIs")
    print("  2. Test GET /api/users to see all users")
    print(f"  3. Test GET /api/users/{user_ids[0]}/profile to see first user's profile")
    print("  4. Ready to implement skill extraction! 🚀")


if __name__ == "__main__":
    main()
