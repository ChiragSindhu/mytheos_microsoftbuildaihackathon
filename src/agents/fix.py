"""Fix Agent - Generates code fixes."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent

class FixAgent(BaseAgent):
    """Agent responsible for generating fixes."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Fix", temperature=0.4, **kwargs)
    
    def get_system_prompt(self) -> str:
        return """You are an expert software engineer. Your role is to:

1. Generate precise code fixes for identified bugs
2. Ensure fixes address root cause, not symptoms
3. Maintain code quality and style
4. Consider edge cases
5. Provide multiple fix options if applicable

Output JSON with:
- primary_fix: Main fix with file path, original code, fixed code
- alternative_fixes: List of alternative approaches
- explanation: Why this fix works
- considerations: Edge cases, potential issues"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fix."""
        user_message = f"""
Root Cause Analysis:
{context.get('root_cause_analysis', '')}

Relevant Code:
{context.get('relevant_code', '')}

Repository Context:
Language: {context.get('language', 'Unknown')}
Frameworks: {context.get('frameworks', [])}

Generate a fix for this bug.
"""
        
        fix_proposal = self.generate(user_message)
        
        return {
            "agent": self.name,
            "fix_proposal": fix_proposal,
            "status": "completed"
        }