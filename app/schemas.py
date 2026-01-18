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


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional for partial updates)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = None
    education: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    target_role: Optional[str] = None
    target_sector: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class ResumeUpload(BaseModel):
    """Schema for resume text upload."""
    resume_text: str = Field(..., min_length=100, description="Resume content as text")


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
    resume_path: Optional[str]
    has_resume: bool = False
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


class CourseUpdate(BaseModel):
    """Schema for updating a course (all fields optional for partial updates)."""
    course_name: Optional[str] = Field(None, min_length=3)
    platform: Optional[str] = None
    instructor: Optional[str] = None
    grade: Optional[str] = None
    completion_date: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
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


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional for partial updates)."""
    project_name: Optional[str] = Field(None, min_length=3)
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
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


# ===== JOB SCHEMAS =====
class JobSearchRequest(BaseModel):
    """Schema for job search request."""
    title: str = Field(default="Healthcare Data Analyst")
    location: str = Field(default="United States")
    limit: int = Field(default=50, le=100)


class JobResponse(BaseModel):
    """Schema for job response."""
    id: str
    title: str
    company: str
    location: str
    description: Optional[str]
    posted_date: Optional[str]
    salary: Optional[str]
    url: Optional[str]


# ===== GAP ANALYSIS SCHEMAS =====
class SkillGap(BaseModel):
    """Schema for skill gap information."""
    skill: str
    user_proficiency: float
    market_requirement: float
    gap: float
    priority: str
    impact: Optional[str]


class GapAnalysisResponse(BaseModel):
    """Schema for gap analysis response."""
    user_id: int
    target_role: str
    overall_readiness: float
    critical_gaps: List[SkillGap]
    important_gaps: List[SkillGap]
    strengths: List[SkillGap]


# ===== COURSE RECOMMENDATION SCHEMAS =====
class CourseRecommendation(BaseModel):
    """Schema for course recommendation."""
    course_name: str
    platform: str
    url: str
    description: Optional[str]
    skill_targeted: str
    rating: Optional[float]
    duration: Optional[str]
    cost: Optional[str]
