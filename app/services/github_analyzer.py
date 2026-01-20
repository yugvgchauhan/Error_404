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
    
    def extract_info_from_url(self, github_url: str) -> Dict:
        """Extract GitHub username and optionally repository name from URL."""
        if not github_url:
            return {'username': None, 'repo_name': None}
        
        # Clean URL
        url_path = github_url.split('github.com/')[-1].split('?')[0].strip('/')
        parts = url_path.split('/')
        
        info = {'username': None, 'repo_name': None}
        if len(parts) >= 1:
            info['username'] = parts[0]
        if len(parts) >= 2:
            # Avoid cases like 'sponsors', 'projects', etc. which aren't repo names in user context
            if parts[1] not in ['repositories', 'projects', 'packages', 'stars', 'followers', 'following']:
                info['repo_name'] = parts[1]
            
        return info
    
    def fetch_user_repos(self, username: str, max_repos: int = 10) -> List[Dict]:
        """
        Fetch public repositories for a GitHub user.
        Uses GitHub REST API.
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
            url = f"https://api.github.com/users/{username}/repos"
            params = {'sort': 'updated', 'per_page': max_repos, 'type': 'owner'}
            headers = {
                'User-Agent': 'Healthcare-Skill-Intelligence-App',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                repos = response.json()
                with open(cache_file, 'w') as f:
                    json.dump(repos, f, indent=2)
                return repos
            return []
        except Exception as e:
            print(f"❌ Error fetching GitHub repos: {e}")
            return []

    def fetch_single_repo(self, username: str, repo_name: str) -> Optional[Dict]:
        """Fetch data for a single specific repository."""
        print(f"🔍 Fetching specific GitHub repo: {username}/{repo_name}...")
        try:
            url = f"https://api.github.com/repos/{username}/{repo_name}"
            headers = {
                'User-Agent': 'Healthcare-Skill-Intelligence-App',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error fetching single repo: {e}")
            return None
    
    def fetch_readme(self, username: str, repo_name: str) -> Optional[str]:
        """
        Fetch README content from a repository using GitHub API.
        """
        print(f"   📄 Fetching README for {repo_name}...")
        try:
            url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
            headers = {
                'User-Agent': 'Healthcare-Skill-Intelligence-App',
                'Accept': 'application/vnd.github.v3.raw'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            print(f"   ❌ Error fetching README: {e}")
            return None
    
    def extract_skills_from_repo(self, repo_data: Dict, readme_content: Optional[str] = None) -> Tuple[List[str], Dict]:
        """Extract skills from repository metadata and README."""
        all_text = ""
        metadata = {
            'repo_name': repo_data.get('name', ''),
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language', ''),
            'topics': repo_data.get('topics', []),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0)
        }
        
        all_text += f"{metadata['repo_name']} {metadata['description']} {metadata['language']} {' '.join(metadata['topics'])} "
        
        if readme_content:
            all_text += readme_content[:5000] + " "
        
        skills = self.skill_extractor.extract_skills_from_text(all_text)
        return (skills, metadata)
    
    def analyze_github_profile(
        self, 
        github_url: str, 
        max_repos: int = 10,
        fetch_readmes: bool = True,
        llm_extractor = None
    ) -> Dict:
        """Complete GitHub profile or repository analysis."""
        info = self.extract_info_from_url(github_url)
        username = info['username']
        specific_repo = info['repo_name']
        
        if not username:
            return {'error': 'Invalid GitHub URL', 'username': None, 'skills_found': {}}
        
        # Determine which repos to analyze
        repos = []
        if specific_repo:
            repo_data = self.fetch_single_repo(username, specific_repo)
            if repo_data:
                repos = [repo_data]
            else:
                return {'error': f'Repository {username}/{specific_repo} not found', 'username': username}
        else:
            repos = self.fetch_user_repos(username, max_repos)
        
        if not repos:
            return {'username': username, 'total_repos': 0, 'repos_analyzed': 0, 'skills_found': {}, 'repo_details': []}
        
        all_skills = {}
        repo_details = []
        
        for repo in repos:
            repo_name = repo.get('name', 'unknown')
            readme_content = self.fetch_readme(username, repo_name) if fetch_readmes else None
            
            # Extract skills using NLP
            skills, metadata = self.extract_skills_from_repo(repo, readme_content)
            
            # Use LLM for deeper analysis if available
            if llm_extractor and (metadata['description'] or readme_content):
                print(f"   🤖 Refining skills for {repo_name} using LLM...")
                context = f"Repo: {repo_name}. Description: {metadata['description']}. Language: {metadata['language']}. Topics: {metadata['topics']}."
                if readme_content:
                    context += f"\nREADME Snapshot: {readme_content[:3000]}"
                
                llm_skills = llm_extractor.extract_skills_with_proficiency(context)
                for item in llm_skills:
                    s_name = item['skill_name']
                    s_prof = item['proficiency']
                    s_conf = item['confidence']
                    
                    if s_name not in all_skills or s_prof > all_skills[s_name][0]:
                        all_skills[s_name] = (s_prof, s_conf)
                    if s_name not in skills:
                        skills.append(s_name)
            
            # Calculate proficiency for non-LLM found skills or base values
            base_proficiency = 0.65
            confidence = 0.75
            
            stars = metadata['stars']
            if stars > 10: base_proficiency += 0.10; confidence += 0.05
            elif stars > 0: base_proficiency += 0.05
            
            proficiency = min(base_proficiency, 0.90)
            confidence = min(confidence, 0.95)
            
            for skill in skills:
                if skill not in all_skills:
                    all_skills[skill] = (proficiency, confidence)
                else:
                    existing_prof, existing_conf = all_skills[skill]
                    all_skills[skill] = (max(existing_prof, proficiency), max(existing_conf, confidence))
            
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
            'repo_name': specific_repo,
            'total_repos': len(repos),
            'repos_analyzed': len(repo_details),
            'skills_found': all_skills,
            'repo_details': repo_details
        }