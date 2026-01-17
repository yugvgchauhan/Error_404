"""Project endpoints router."""
import json
from fastapi import APIRouter, HTTPException
from typing import List

from app.database import get_db
from app import schemas

router = APIRouter(prefix="/api/users/{user_id}/projects", tags=["Projects"])


@router.post("", response_model=schemas.ProjectResponse)
def add_project(user_id: int, project: schemas.ProjectCreate):
    """Add a project for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Insert project
        tech_stack_json = json.dumps(project.tech_stack) if project.tech_stack else None
        
        cursor.execute('''
            INSERT INTO projects (user_id, project_name, description, tech_stack, role, 
                                team_size, duration, github_link, deployed_link, 
                                project_type, impact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, project.project_name, project.description, tech_stack_json,
              project.role, project.team_size, project.duration, project.github_link,
              project.deployed_link, project.project_type, project.impact))
        
        project_id = cursor.lastrowid
        
        # Get created project
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        if result.get('tech_stack'):
            result['tech_stack'] = json.loads(result['tech_stack'])
        if result.get('skills_extracted'):
            result['skills_extracted'] = json.loads(result['skills_extracted'])
        
        return result


@router.get("", response_model=List[schemas.ProjectResponse])
def get_user_projects(user_id: int):
    """Get all projects for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get projects
        cursor.execute("SELECT * FROM projects WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            project = dict(row)
            if project.get('tech_stack'):
                project['tech_stack'] = json.loads(project['tech_stack'])
            if project.get('skills_extracted'):
                project['skills_extracted'] = json.loads(project['skills_extracted'])
            projects.append(project)
        
        return projects


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(user_id: int, project_id: int):
    """Get a specific project by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get project
        cursor.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = dict(row)
        if project.get('tech_stack'):
            project['tech_stack'] = json.loads(project['tech_stack'])
        if project.get('skills_extracted'):
            project['skills_extracted'] = json.loads(project['skills_extracted'])
        
        return project


@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(user_id: int, project_id: int, project: schemas.ProjectUpdate):
    """Update a project. Only provided fields will be updated."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify project exists and belongs to user
        cursor.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get only the fields that were actually provided (not None)
        update_data = project.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Handle tech_stack serialization if provided
        if 'tech_stack' in update_data and update_data['tech_stack'] is not None:
            update_data['tech_stack'] = json.dumps(update_data['tech_stack'])
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        values.append(project_id)
        query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, values)
        
        # Get updated project
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        result = dict(row)
        if result.get('tech_stack'):
            result['tech_stack'] = json.loads(result['tech_stack'])
        if result.get('skills_extracted'):
            result['skills_extracted'] = json.loads(result['skills_extracted'])
        
        return result


@router.delete("/{project_id}")
def delete_project(user_id: int, project_id: int):
    """Delete a project."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify project exists and belongs to user
        cursor.execute("SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete project
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        
        return {"message": "Project deleted successfully", "project_id": project_id}
