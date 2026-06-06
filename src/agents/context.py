"""Context Agent - Gathers historical and environmental context."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent
from src.tools.github_client import GitHubClient

class ContextAgent(BaseAgent):
    """Agent responsible for gathering contextual information."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Context", temperature=0.5, **kwargs)
        self.github_client = GitHubClient()
    
    def get_system_prompt(self) -> str:
        return """You are an expert at gathering contextual information. Your role is to:

1. Analyze recent commits and changes
2. Review related pull requests
3. Find similar past issues
4. Identify recent dependency changes
5. Understand project patterns and conventions

Output structured context in JSON:
- recent_changes: Relevant commits
- related_issues: Similar past bugs
- dependencies_updates: Recent dependency changes
- patterns: Project coding patterns
- environmental_factors: Deployment, config changes"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather contextual information."""
        
        repo_url = context.get('repo_url', '')
        
        # Get recent commits (would use GitHub API in production)
        recent_commits = self._get_recent_commits(repo_url, context)
        
        user_message = f"""
Repository: {repo_url}
Error: {context.get('error_log', '')}

Recent Commits:
{recent_commits}

Affected Files:
{context.get('analyzed_files', [])}

Gather contextual information:
1. What recent changes might have introduced this bug?
2. Have similar issues occurred before?
3. Were dependencies recently updated?
4. What are the project patterns we should follow?
"""
        
        context_info = self.generate(user_message)
        
        return {
            "agent": self.name,
            "context_info": context_info,
            "recent_commits": recent_commits,
            "status": "completed"
        }
    
    def _get_recent_commits(self, repo_url: str, context: Dict[str, Any]) -> str:
        """Get recent commits (mock for now)."""
        # In production, this would use GitHubClient
        return """
Recent commits:
- abc123: Update user API endpoint (2 days ago)
- def456: Add null check in order processing (3 days ago)
- ghi789: Refactor authentication middleware (5 days ago)
"""