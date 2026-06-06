"""Git operations."""
import subprocess
from pathlib import Path
from typing import List, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class GitOperations:
    """Handle git operations."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def clone(self, repo_url: str, target_dir: Optional[str] = None) -> bool:
        """Clone a repository."""
        try:
            target = target_dir or self.repo_path
            subprocess.run(
                ['git', 'clone', repo_url, str(target)],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e}")
            return False
    
    def get_recent_commits(self, limit: int = 10) -> List[dict]:
        """Get recent commits."""
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%s|%ad'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.split('\n'):
                if line:
                    hash, author, subject, date = line.split('|')
                    commits.append({
                        'hash': hash,
                        'author': author,
                        'subject': subject,
                        'date': date
                    })
            return commits
        except Exception as e:
            logger.error(f"Failed to get commits: {e}")
            return []