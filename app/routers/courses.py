"""Course endpoints router."""
import json
from fastapi import APIRouter, HTTPException
from typing import List

from app.database import get_db
from app import schemas

router = APIRouter(prefix="/api/users/{user_id}/courses", tags=["Courses"])


@router.post("", response_model=schemas.CourseResponse)
def add_course(user_id: int, course: schemas.CourseCreate):
    """Add a course for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Insert course
        cursor.execute('''
            INSERT INTO courses (user_id, course_name, platform, instructor, grade, 
                               completion_date, duration, description, certificate_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, course.course_name, course.platform, course.instructor, 
              course.grade, course.completion_date, course.duration, 
              course.description, course.certificate_url))
        
        course_id = cursor.lastrowid
        
        # Get created course
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        if result.get('skills_extracted'):
            result['skills_extracted'] = json.loads(result['skills_extracted'])
        
        return result


@router.get("", response_model=List[schemas.CourseResponse])
def get_user_courses(user_id: int):
    """Get all courses for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get courses
        cursor.execute("SELECT * FROM courses WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        courses = []
        for row in rows:
            course = dict(row)
            if course.get('skills_extracted'):
                course['skills_extracted'] = json.loads(course['skills_extracted'])
            courses.append(course)
        
        return courses


@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(user_id: int, course_id: int):
    """Get a specific course by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get course
        cursor.execute("SELECT * FROM courses WHERE id = ? AND user_id = ?", (course_id, user_id))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")
        
        course = dict(row)
        if course.get('skills_extracted'):
            course['skills_extracted'] = json.loads(course['skills_extracted'])
        
        return course


@router.put("/{course_id}", response_model=schemas.CourseResponse)
def update_course(user_id: int, course_id: int, course: schemas.CourseUpdate):
    """Update a course. Only provided fields will be updated."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify course exists and belongs to user
        cursor.execute("SELECT * FROM courses WHERE id = ? AND user_id = ?", (course_id, user_id))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Get only the fields that were actually provided (not None)
        update_data = course.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        values.append(course_id)
        query = f"UPDATE courses SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, values)
        
        # Get updated course
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        if result.get('skills_extracted'):
            result['skills_extracted'] = json.loads(result['skills_extracted'])
        
        return result


@router.delete("/{course_id}")
def delete_course(user_id: int, course_id: int):
    """Delete a course."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify course exists and belongs to user
        cursor.execute("SELECT id FROM courses WHERE id = ? AND user_id = ?", (course_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Delete course
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        
        return {"message": "Course deleted successfully", "course_id": course_id}
