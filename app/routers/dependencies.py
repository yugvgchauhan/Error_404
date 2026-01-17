"""Dependencies for routers - shared services and configurations."""
import os
from functools import lru_cache
from dotenv import load_dotenv

from app.database import get_db, init_db
from app.services.skill_extractor import SkillExtractor
from app.services.resume_parser import ResumeParser
from app.services.linkedin_job_fetcher import LinkedInJobFetcher
from app.services.job_skill_analyzer import JobSkillAnalyzer
from app.services.gap_analyzer import GapAnalyzer
from app.services.course_recommender import CourseRecommender
from app.services.github_analyzer import GitHubAnalyzer

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Configuration
UPLOAD_DIR = "uploads/resumes"
SKILLS_FILE = os.path.join("app", "data", "healthcare_skills.json")


class ServiceContainer:
    """Container for all services - enables dependency injection and lazy loading."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Initialize core services
        self._skill_extractor = SkillExtractor(SKILLS_FILE)
        self._resume_parser = ResumeParser()
        
        # Load API keys from environment
        self._rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
        self._tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        
        # Log API key status
        print(f"🔑 RAPIDAPI_KEY loaded: {'Yes' if self._rapidapi_key else 'No'}")
        print(f"🔑 TAVILY_API_KEY loaded: {'Yes' if self._tavily_api_key else 'No'}")
        
        # Initialize dependent services
        self._linkedin_fetcher = LinkedInJobFetcher(self._rapidapi_key) if self._rapidapi_key else None
        self._job_analyzer = JobSkillAnalyzer(self._skill_extractor)
        self._gap_analyzer = GapAnalyzer()
        self._course_recommender = CourseRecommender(self._tavily_api_key)
        self._github_analyzer = GitHubAnalyzer(self._skill_extractor)
        
        self._initialized = True
    
    @property
    def skill_extractor(self) -> SkillExtractor:
        return self._skill_extractor
    
    @property
    def resume_parser(self) -> ResumeParser:
        return self._resume_parser
    
    @property
    def linkedin_fetcher(self) -> LinkedInJobFetcher:
        return self._linkedin_fetcher
    
    @property
    def job_analyzer(self) -> JobSkillAnalyzer:
        return self._job_analyzer
    
    @property
    def gap_analyzer(self) -> GapAnalyzer:
        return self._gap_analyzer
    
    @property
    def course_recommender(self) -> CourseRecommender:
        return self._course_recommender
    
    @property
    def github_analyzer(self) -> GitHubAnalyzer:
        return self._github_analyzer
    
    @property
    def upload_dir(self) -> str:
        return UPLOAD_DIR
    
    def has_linkedin_api(self) -> bool:
        """Check if LinkedIn API is configured."""
        return self._linkedin_fetcher is not None
    
    def has_tavily_api(self) -> bool:
        """Check if Tavily API is configured."""
        return bool(self._tavily_api_key)


@lru_cache()
def get_services() -> ServiceContainer:
    """Get the service container singleton."""
    return ServiceContainer()


def get_sample_market_requirements() -> dict:
    """Return sample market requirements when API is unavailable.
    
    This is used as a fallback when LinkedIn API is not configured.
    In production, this should be replaced with cached real market data.
    """
    return {
        "python": {"frequency": 0.85, "requirement_level": "critical", "avg_proficiency_needed": 0.75},
        "sql": {"frequency": 0.80, "requirement_level": "critical", "avg_proficiency_needed": 0.70},
        "machine-learning": {"frequency": 0.65, "requirement_level": "important", "avg_proficiency_needed": 0.65},
        "data-analysis": {"frequency": 0.75, "requirement_level": "critical", "avg_proficiency_needed": 0.70},
        "tensorflow": {"frequency": 0.45, "requirement_level": "important", "avg_proficiency_needed": 0.60},
        "healthcare-data": {"frequency": 0.55, "requirement_level": "important", "avg_proficiency_needed": 0.65},
        "nlp": {"frequency": 0.40, "requirement_level": "emerging", "avg_proficiency_needed": 0.55},
        "pandas": {"frequency": 0.70, "requirement_level": "critical", "avg_proficiency_needed": 0.70},
        "tableau": {"frequency": 0.50, "requirement_level": "important", "avg_proficiency_needed": 0.60},
        "statistics": {"frequency": 0.60, "requirement_level": "important", "avg_proficiency_needed": 0.65},
    }
