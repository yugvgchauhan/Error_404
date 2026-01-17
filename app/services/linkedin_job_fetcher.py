"""LinkedIn job fetcher using RapidAPI."""
import os
import http.client
import json
import urllib.parse
from typing import List, Dict, Optional
from datetime import datetime


class LinkedInJobFetcher:
    """Fetch jobs from LinkedIn using RapidAPI."""
    
    def __init__(self, api_key: str):
        """Initialize with RapidAPI key."""
        self.api_key = api_key
        self.host = "linkedin-job-search-api.p.rapidapi.com"
        self.cache_dir = "app/data/cached_jobs"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_filename(self, title: str, location: str) -> str:
        """Generate cache filename from search parameters."""
        safe_title = title.replace(' ', '_').replace('/', '_')
        safe_location = location.replace(' ', '_').replace('/', '_')
        return f"{safe_title}_{safe_location}.json"
    
    def _load_from_cache(self, title: str, location: str) -> Optional[Dict]:
        """Load jobs from cache if available and fresh (< 24 hours)."""
        cache_file = os.path.join(
            self.cache_dir,
            self._get_cache_filename(title, location)
        )
        
        if os.path.exists(cache_file):
            # Check file age
            file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            
            # Cache valid for 24 hours
            if file_age < 24 * 3600:
                print(f"📦 Loading jobs from cache (age: {file_age/3600:.1f} hours)")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return None
    
    def _save_to_cache(self, title: str, location: str, jobs_data: Dict):
        """Save jobs to cache."""
        cache_file = os.path.join(
            self.cache_dir,
            self._get_cache_filename(title, location)
        )
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved jobs to cache: {cache_file}")
    
    def fetch_jobs(
        self,
        title: str,
        location: str = "United States",
        limit: int = 50,
        offset: int = 0,
        use_cache: bool = True
    ) -> Dict:
        """
        Fetch jobs from LinkedIn API.
        
        Args:
            title: Job title to search for (e.g., "Healthcare Data Analyst")
            location: Location filter (e.g., "United States", "India")
            limit: Number of jobs to fetch (max: 100)
            offset: Offset for pagination
            use_cache: Whether to use cached results
        
        Returns:
            {
                'jobs': [...],
                'total': int,
                'search_params': {...},
                'cached': bool,
                'timestamp': str
            }
        """
        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(title, location)
            if cached_data:
                cached_data['cached'] = True
                return cached_data
        
        print(f"🔍 Fetching jobs from LinkedIn API...")
        print(f"   Title: {title}")
        print(f"   Location: {location}")
        print(f"   Limit: {limit}")
        
        try:
            conn = http.client.HTTPSConnection(self.host)
            
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.host
            }
            
            # URL encode with quotes around values (API requires this format)
            # Format: %22value%22 where %22 is URL-encoded quote
            title_encoded = urllib.parse.quote(f'"{title}"')
            location_encoded = urllib.parse.quote(f'"{location}"')
            
            # Build endpoint with proper encoding
            endpoint = f"/active-jb-24h?limit={limit}&offset={offset}&title_filter={title_encoded}&location_filter={location_encoded}&description_type=text"
            
            print(f"   Endpoint: {endpoint}")
            
            # Make request
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            print(f"   Response status: {res.status}")
            
            # Parse response
            json_data = json.loads(data)
            
            # Process response
            if 'data' in json_data:
                jobs = json_data['data']
            elif isinstance(json_data, list):
                jobs = json_data
            else:
                jobs = []
            
            result = {
                'jobs': jobs,
                'total': len(jobs),
                'search_params': {
                    'title': title,
                    'location': location,
                    'limit': limit
                },
                'cached': False,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to cache
            if use_cache and jobs:
                self._save_to_cache(title, location, result)
            
            print(f"✅ Fetched {len(jobs)} jobs from LinkedIn")
            
            return result
        
        except Exception as e:
            print(f"❌ Error fetching jobs from LinkedIn: {e}")
            return {
                'jobs': [],
                'total': 0,
                'error': str(e),
                'cached': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_job_details(self, jobs_data: Dict) -> List[Dict]:
        """
        Extract essential details from jobs data.
        
        Returns list of:
            {
                'id': str,
                'title': str,
                'company': str,
                'location': str,
                'description': str,
                'posted_date': str,
                'salary': Optional[str],
                'url': str,
                'seniority': str,
                'employment_type': str,
                'industry': str
            }
        """
        jobs = jobs_data.get('jobs', [])
        
        extracted_jobs = []
        
        for job in jobs:
            # Get location - try locations_derived first, then fall back
            location = 'Unknown Location'
            if job.get('locations_derived'):
                location = job['locations_derived'][0] if isinstance(job['locations_derived'], list) else job['locations_derived']
            elif job.get('location'):
                location = job['location']
            
            # Get employment type
            employment_type = 'Full-time'
            if job.get('employment_type'):
                emp_types = job['employment_type']
                if isinstance(emp_types, list):
                    employment_type = ', '.join([t.replace('_', ' ').title() for t in emp_types])
                else:
                    employment_type = emp_types.replace('_', ' ').title()
            
            extracted_jobs.append({
                'id': str(job.get('id', job.get('job_id', 'unknown'))),
                'title': job.get('title', 'Unknown Title'),
                'company': job.get('organization', job.get('company', job.get('company_name', 'Unknown Company'))),
                'location': location,
                'description': job.get('description_text', job.get('description', '')),
                'posted_date': job.get('date_posted', job.get('posted_at', job.get('posted_date', 'Unknown'))),
                'salary': job.get('salary_raw', job.get('salary', job.get('salary_range', None))),
                'url': job.get('url', job.get('job_url', '#')),
                'seniority': job.get('seniority', 'Not specified'),
                'employment_type': employment_type,
                'industry': job.get('linkedin_org_industry', 'Unknown')
            })
        
        return extracted_jobs