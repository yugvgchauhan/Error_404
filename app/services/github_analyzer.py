"""GitHub repository analyzer to extract skills from public repos."""
import os
import re
import json
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class GitHubAnalyzer:
    """Fetch and analyze GitHub repositories to extract skills."""
    
    def __init__(self, skill_extractor):
        """Initialize with skill extractor for skill matching."""
        self.skill_extractor = skill_extractor
        self.cache_dir = "app/data/github_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def extract_username_from_url(self, github_url: str) -> Optional[str]:
        """Extract GitHub username from URL."""
        if not github_url:
            return None
        
        # Pattern: https://github.com/username
        pattern = r'github\.com/([^/\s]+)'
        match = re.search(pattern, github_url)
        
        if match:
            return match.group(1)
        return None
    
    def fetch_user_repos(self, username: str, max_repos: int = 10) -> List[Dict]:
        """
        Fetch public repositories for a GitHub user.
        Uses GitHub REST API (no auth required for public repos).
        """
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"{username}_repos.json")
        
        if os.path.exists(cache_file):
            # Check if cache is less than 7 days old
            file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            if file_age < 7 * 24 * 3600:  # 7 days
                print(f"📦 Loading GitHub repos from cache for {username}")
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        print(f"🔍 Fetching GitHub repos for {username}...")
        
        try:
            # GitHub API endpoint
            url = f"https://api.github.com/users/{username}/repos"
            
            # Parameters
            params = {
                'sort': 'updated',
                'per_page': max_repos,
                'type': 'owner'  # Only repos owned by user
            }
            
            # Headers (User-Agent required by GitHub)
            headers = {
                'User-Agent': 'Healthcare-Skill-Intelligence-App',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                repos = response.json()
                
                # Cache the response
                with open(cache_file, 'w') as f:
                    json.dump(repos, f, indent=2)
                
                print(f"✅ Fetched {len(repos)} repositories")
                return repos
            
            elif response.status_code == 404:
                print(f"❌ GitHub user '{username}' not found")
                return []
            
            else:
                print(f"❌ GitHub API error: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"❌ Error fetching GitHub repos: {e}")
            return []
    
    def fetch_readme(self, username: str, repo_name: str) -> Optional[str]:
        """Fetch README content from a repository."""
        print(f"   📄 Fetching README for {repo_name}...")
        
        try:
            # Try common README filenames
            readme_names = ['README.md', 'README.MD', 'Readme.md', 'readme.md', 'README.txt', 'README']
            
            for readme_name in readme_names:
                url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{readme_name}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    return response.text
                
                # Try 'master' branch if 'main' doesn't work
                url = f"https://raw.githubusercontent.com/{username}/{repo_name}/master/{readme_name}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    return response.text
            
            print(f"   ⚠️ README not found for {repo_name}")
            return None
        
        except Exception as e:
            print(f"   ❌ Error fetching README: {e}")
            return None
    
    def extract_skills_from_repo(self, repo_data: Dict, readme_content: Optional[str] = None) -> Tuple[List[str], Dict]:
        """
        Extract skills from repository metadata and README.
        
        Returns:
            (skills_list, metadata)
        """
        all_text = ""
        metadata = {
            'repo_name': repo_data.get('name', ''),
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language', ''),
            'topics': repo_data.get('topics', []),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0)
        }
        
        # 1. Extract from repository name
        all_text += repo_data.get('name', '') + " "
        
        # 2. Extract from description
        if repo_data.get('description'):
            all_text += repo_data['description'] + " "
        
        # 3. Extract from primary language
        if repo_data.get('language'):
            all_text += repo_data['language'] + " "
        
        # 4. Extract from topics/tags
        if repo_data.get('topics'):
            all_text += " ".join(repo_data['topics']) + " "
        
        # 5. Extract from README
        if readme_content:
            # Limit README to first 2000 characters to avoid too much noise
            all_text += readme_content[:2000] + " "
        
        # Use skill extractor to find matching skills
        skills = self.skill_extractor.extract_skills_from_text(all_text)
        
        return (skills, metadata)
    
    def analyze_github_profile(
        self, 
        github_url: str, 
        max_repos: int = 10,
        fetch_readmes: bool = True
    ) -> Dict:
        """
        Complete GitHub profile analysis.
        
        Returns:
            {
                'username': str,
                'total_repos': int,
                'repos_analyzed': int,
                'skills_found': {skill: (proficiency, confidence)},
                'repo_details': [...]
            }
        """
        username = self.extract_username_from_url(github_url)
        
        if not username:
            return {
                'error': 'Invalid GitHub URL',
                'username': None,
                'skills_found': {}
            }
        
        # Fetch repositories
        repos = self.fetch_user_repos(username, max_repos)
        
        if not repos:
            return {
                'username': username,
                'total_repos': 0,
                'repos_analyzed': 0,
                'skills_found': {},
                'repo_details': []
            }
        
        # Analyze each repository
        all_skills = {}
        repo_details = []
        
        for repo in repos:
            repo_name = repo.get('name', 'unknown')
            
            # Fetch README if enabled
            readme_content = None
            if fetch_readmes:
                readme_content = self.fetch_readme(username, repo_name)
            
            # Extract skills
            skills, metadata = self.extract_skills_from_repo(repo, readme_content)
            
            # Calculate proficiency based on repo quality indicators
            base_proficiency = 0.65  # GitHub projects show practical skills
            confidence = 0.75
            
            # Boost for stars (community validation)
            stars = metadata['stars']
            if stars > 50:
                base_proficiency += 0.15
                confidence += 0.10
            elif stars > 10:
                base_proficiency += 0.10
                confidence += 0.05
            elif stars > 0:
                base_proficiency += 0.05
            
            # Boost for forks (others building on it)
            if metadata['forks'] > 10:
                base_proficiency += 0.10
            
            # Cap proficiency
            proficiency = min(base_proficiency, 0.90)
            confidence = min(confidence, 0.95)
            
            # Store skills with proficiency
            for skill in skills:
                if skill not in all_skills:
                    all_skills[skill] = (proficiency, confidence)
                else:
                    # Take max proficiency if skill appears in multiple repos
                    existing_prof, existing_conf = all_skills[skill]
                    all_skills[skill] = (
                        max(existing_prof, proficiency),
                        max(existing_conf, confidence)
                    )
            
            repo_details.append({
                'name': repo_name,
                'description': metadata['description'],
                'language': metadata['language'],
                'stars': metadata['stars'],
                'forks': metadata['forks'],
                'skills_found': skills,
                'url': repo.get('html_url', '')
            })
            
            print(f"   ✅ {repo_name}: {len(skills)} skills found")
        
        return {
            'username': username,
            'total_repos': len(repos),
            'repos_analyzed': len(repo_details),
            'skills_found': all_skills,
            'repo_details': repo_details
        }