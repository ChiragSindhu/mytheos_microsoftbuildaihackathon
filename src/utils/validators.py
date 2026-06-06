"""Input validators."""
import re
from typing import Optional
from urllib.parse import urlparse

def validate_repo_url(repo_url: str) -> bool:
    """Validate GitHub repository URL."""
    patterns = [
        r'^https://github\.com/[\w-]+/[\w-]+/?$',
        r'^git@github\.com:[\w-]+/[\w-]+\.git$',
        r'^https://github\.com/[\w-]+/[\w-]+\.git$',
    ]
    
    return any(re.match(pattern, repo_url) for pattern in patterns)

def validate_error_log(error_log: str) -> bool:
    """Validate error log has content."""
    return bool(error_log and error_log.strip())

def extract_repo_info(repo_url: str) -> Optional[dict]:
    """Extract owner and repo name from URL."""
    if not validate_repo_url(repo_url):
        return None
    
    # Parse URL
    if repo_url.startswith('git@'):
        # git@github.com:owner/repo.git
        match = re.match(r'git@github\.com:([\w-]+)/([\w-]+)(?:\.git)?', repo_url)
    else:
        # https://github.com/owner/repo
        match = re.match(r'https://github\.com/([\w-]+)/([\w-]+)', repo_url)
    
    if match:
        return {
            'owner': match.group(1),
            'repo': match.group(2).replace('.git', '')
        }
    
    return None