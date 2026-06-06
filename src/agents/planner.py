"""Planner Agent - Creates debugging strategy."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent responsible for creating debugging plans."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Planner", **kwargs)
    
    def get_system_prompt(self) -> str:
        return """You are an expert debugging strategist. Your role is to analyze error reports 
and repository information to create a comprehensive debugging plan.

Given:
- Repository structure
- Error logs/stack traces
- Programming language
- Available context

Create a detailed debugging plan that includes:
1. Error classification (syntax, runtime, logic, integration, etc.)
2. Affected components/files
3. Investigation strategy
4. Reproduction steps
5. Likely root cause hypotheses
6. Suggested fixes approach

Output your plan in clear, structured JSON format."""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a debugging plan."""
        user_message = f"""
Repository: {context.get('repo_name', 'Unknown')}
Language: {context.get('language', 'Unknown')}
Files: {len(context.get('files', []))}

Error Log:
{context.get('error_log', 'No error log provided')}

Repository Structure:
{context.get('repo_structure', 'Not provided')}

Create a detailed debugging plan for this issue.
"""
        
        plan_json = self.generate(user_message)
        
        return {
            "agent": self.name,
            "plan": plan_json,
            "status": "completed"
        }