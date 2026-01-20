"""User endpoints router."""
from fastapi import APIRouter, HTTPException
from typing import List

from app.database import get_db
from app import schemas

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate):
    """
    Register a new user.
    
    - **name**: User's full name
    - **email**: User's email (must be unique)
    - **education**: Degree and major
    - **target_role**: Target healthcare role
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (name, email, education, university, graduation_year, location, 
                             target_role, target_sector, phone, linkedin_url, github_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user.name, user.email, user.education, user.university, user.graduation_year,
              user.location, user.target_role, user.target_sector, user.phone, 
              user.linkedin_url, user.github_url))
        
        user_id = cursor.lastrowid
        
        # Get created user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        return dict(row)


@router.get("/email/{email}", response_model=schemas.UserResponse)
def get_user_by_email(email: str):
    """Get user by email (used for login)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = dict(row)
        user['has_resume'] = bool(user.get('resume_path'))
        return user


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int):
    """Get user by ID with completion stats."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = dict(row)
        user['has_resume'] = bool(user.get('resume_path'))
        
        # Get stats for completion calculation
        cursor.execute("SELECT COUNT(*) as count FROM user_skills WHERE user_id = ?", (user_id,))
        total_skills = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE user_id = ?", (user_id,))
        total_projects = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE user_id = ?", (user_id,))
        total_courses = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM certifications WHERE user_id = ?", (user_id,))
        total_certifications = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM work_experience WHERE user_id = ?", (user_id,))
        total_work_experience = cursor.fetchone()['count']
        
        # Calculate profile completion
        completion_fields = [
            bool(user.get('name')),
            bool(user.get('education')),
            bool(user.get('university')),
            bool(user.get('graduation_year')),
            bool(user.get('location')),
            bool(user.get('target_role')),
            bool(user.get('phone')),
            bool(user.get('linkedin_url')),
            bool(user.get('github_url')),
            bool(user.get('resume_path')),
            total_skills > 0,
            total_projects > 0,
            total_courses > 0,
            total_certifications > 0,
            total_work_experience > 0
        ]
        
        user['profile_completion'] = round((sum(completion_fields) / len(completion_fields)) * 100, 1)
        user['total_skills'] = total_skills
        user['total_projects'] = total_projects
        user['total_courses'] = total_courses
        
        return user


@router.get("/{user_id}/profile", response_model=schemas.ProfileSummary)
def get_user_profile(user_id: int):
    """Get complete user profile with statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Count related items
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE user_id = ?", (user_id,))
        total_courses = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM projects WHERE user_id = ?", (user_id,))
        total_projects = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM certifications WHERE user_id = ?", (user_id,))
        total_certifications = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM work_experience WHERE user_id = ?", (user_id,))
        total_work_experience = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM user_skills WHERE user_id = ?", (user_id,))
        total_skills = cursor.fetchone()['count']
        
        user = dict(user_row)
        user['has_resume'] = bool(user.get('resume_path'))
        
        # Calculate profile completion with more granularity
        completion_fields = [
            bool(user.get('name')),
            bool(user.get('education')),
            bool(user.get('university')),
            bool(user.get('graduation_year')),
            bool(user.get('location')),
            bool(user.get('target_role')),
            bool(user.get('phone')),
            bool(user.get('linkedin_url')),
            bool(user.get('github_url')),
            bool(user.get('resume_path')),
            total_skills > 0,
            total_projects > 0,
            total_courses > 0,
            total_certifications > 0,
            total_work_experience > 0
        ]
        
        fields_filled = sum(completion_fields)
        # We have 15 fields now. Let's make it 0% if nothing but name is filled (name is required for register)
        # Actually, let's just use the real count.
        profile_completion = round((fields_filled / len(completion_fields)) * 100, 1)
        
        return {
            "user": user,
            "total_courses": total_courses,
            "total_projects": total_projects,
            "total_certifications": total_certifications,
            "total_work_experience": total_work_experience,
            "total_skills": total_skills,
            "profile_completion": profile_completion
        }


@router.get("", response_model=List[schemas.UserResponse])
def list_users(skip: int = 0, limit: int = 100):
    """List all users."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserUpdate):
    """Update user by ID. Only provided fields will be updated."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists and get current data
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        existing_data = dict(existing)
        
        # Get only the fields that were actually provided (not None)
        update_data = user.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Check for email conflict if email is being updated
        if 'email' in update_data and update_data['email']:
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (update_data['email'], user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already in use by another user")
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, values)
        
        # Get updated user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        result['has_resume'] = bool(result.get('resume_path'))
        return result


@router.delete("/{user_id}")
def delete_user(user_id: int):
    """Delete user by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user (cascading will handle related data)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        return {"message": "User deleted successfully", "user_id": user_id}
