"""Review Agent - Acts as senior engineer code reviewer."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent

class ReviewAgent(BaseAgent):
    """Agent responsible for code review."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Review", temperature=0.3, **kwargs)
    
    def get_system_prompt(self) -> str:
        return """You are a senior software engineer performing code review. Your role is to:

1. Review the proposed fix thoroughly
2. Check for security vulnerabilities
3. Verify edge cases are handled
4. Ensure coding standards compliance
5. Assess performance implications
6. Validate test coverage

Output structured review in JSON:
- approval_status: approved|needs_changes|rejected
- security_check: Security concerns
- edge_cases: Edge cases to consider
- performance_impact: Performance analysis
- code_quality: Code quality assessment
- suggestions: Improvement suggestions
- test_coverage_assessment: Test quality review"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review the fix and tests."""
        
        user_message = f"""
Root Cause:
{context.get('root_cause_analysis', '')}

Proposed Fix:
{context.get('fix_proposal', '')}

Generated Tests:
{context.get('test_code', '')}

Original Error:
{context.get('error_log', '')}

Review this fix as a senior engineer:
1. Does it properly address the root cause?
2. Are there any security concerns?
3. Are edge cases handled?
4. Is performance acceptable?
5. Does it follow coding standards?
6. Are tests comprehensive?

Provide approval status and detailed feedback.
"""
        
        review_result = self.generate(user_message)
        
        return {
            "agent": self.name,
            "review_result": review_result,
            "status": "completed"
        }