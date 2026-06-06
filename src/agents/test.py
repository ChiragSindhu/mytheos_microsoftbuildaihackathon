"""Test Agent - Generates comprehensive tests."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent

class TestAgent(BaseAgent):
    """Agent responsible for generating tests."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Test", temperature=0.4, **kwargs)
    
    def get_system_prompt(self) -> str:
        return """You are an expert test engineer. Your role is to:

1. Generate comprehensive test cases
2. Create unit tests for the fix
3. Create integration tests
4. Create regression tests to prevent re-occurrence
5. Include edge cases and boundary conditions

Output JSON with:
- unit_tests: Unit test code
- integration_tests: Integration test code
- regression_tests: Regression test code
- test_cases: List of test scenarios
- coverage_notes: What is tested and what isn't"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test cases."""
        
        user_message = f"""
Root Cause:
{context.get('root_cause_analysis', '')}

Fix Proposal:
{context.get('fix_proposal', '')}

Language: {context.get('language', 'Unknown')}
Testing Framework: {context.get('test_framework', 'pytest')}

Generate comprehensive tests:
1. Unit tests for the fixed code
2. Integration tests for the workflow
3. Regression tests to prevent this bug from reoccurring
4. Edge case tests

Include:
- Test file paths
- Complete test code
- Test descriptions
- Expected outcomes
"""
        
        test_code = self.generate(user_message)
        
        return {
            "agent": self.name,
            "test_code": test_code,
            "status": "completed"
        }