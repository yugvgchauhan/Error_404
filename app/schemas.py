"""Pydantic schemas for request/response validation."""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ===== USER SCHEMAS =====
class UserCreate(BaseModel):
    """Schema for creating a new user."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str
    education: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    target_role: Optional[str] = None
    target_sector: str = "healthcare"
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    name: str
    email: str
    education: Optional[str]
    university: Optional[str]
    graduation_year: Optional[int]
    location: Optional[str]
    target_role: Optional[str]
    target_sector: str
    phone: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== COURSE SCHEMAS =====
class CourseCreate(BaseModel):
    """Schema for adding a course."""
    course_name: str = Field(..., min_length=3)
    platform: Optional[str] = None
    instructor: Optional[str] = None
    grade: Optional[str] = None
    completion_date: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = Field(None, min_length=20)
    certificate_url: Optional[str] = None


class CourseResponse(BaseModel):
    """Schema for course response."""
    id: int
    user_id: int
    course_name: str
    platform: Optional[str]
    description: Optional[str]
    skills_extracted: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== PROJECT SCHEMAS =====
class ProjectCreate(BaseModel):
    """Schema for adding a project."""
    project_name: str = Field(..., min_length=3)
    description: str = Field(..., min_length=50)
    tech_stack: Optional[List[str]] = []
    role: Optional[str] = None
    team_size: Optional[int] = None
    duration: Optional[str] = None
    github_link: Optional[str] = None
    deployed_link: Optional[str] = None
    project_type: Optional[str] = None
    impact: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    user_id: int
    project_name: str
    description: str
    tech_stack: Optional[List[str]]
    skills_extracted: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== SKILL SCHEMAS =====
class UserSkillResponse(BaseModel):
    """Schema for user skill response."""
    id: int
    user_id: int
    skill_name: str
    proficiency: float
    confidence: float
    source_count: int
    sources: Optional[List[str]]
    
    class Config:
        from_attributes = True


# ===== PROFILE SUMMARY =====
class ProfileSummary(BaseModel):
    """Complete user profile summary."""
    user: UserResponse
    total_courses: int
    total_projects: int
    total_certifications: int
    total_work_experience: int
    total_skills: int
    profile_completion: float
