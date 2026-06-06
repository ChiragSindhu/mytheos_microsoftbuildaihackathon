"""GitHub API client."""
from typing import Optional, List, Dict, Any
import requests
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class GitHubClient:
    """GitHub API client."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> str:
        """Get file content from repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        import base64
        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')
    
    def get_commits(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits."""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": limit}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def create_issue(self, owner: str, repo: str, title: str, body: str) -> Dict[str, Any]:
        """Create an issue."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        data = {"title": title, "body": body}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict[str, Any]:
        """Create a pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()