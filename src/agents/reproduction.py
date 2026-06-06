"""Reproduction Agent - Attempts to reproduce the bug."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent
from src.tools.code_executor import CodeExecutor
from src.tools.test_runner import TestRunner

class ReproductionAgent(BaseAgent):
    """Agent responsible for reproducing bugs."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Reproduction", **kwargs)
        self.code_executor = CodeExecutor()
        self.test_runner = TestRunner()
    
    def get_system_prompt(self) -> str:
        return """You are an expert at reproducing software bugs. Your role is to:

1. Analyze the error logs and debugging plan
2. Create minimal reproduction steps
3. Write test cases that trigger the bug
4. Verify the bug is reproducible

Output:
- Reproduction steps (human-readable)
- Minimal code to reproduce
- Test case code
- Reproduction success status"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to reproduce the bug."""
        user_message = f"""
Debugging Plan:
{context.get('plan', 'No plan provided')}

Error Log:
{context.get('error_log', 'No error log')}

Relevant Code:
{context.get('relevant_code', 'No code provided')}

Create a minimal reproduction case and test for this bug.
Output as JSON with fields: steps, reproduction_code, test_code
"""
        
        reproduction_info = self.generate(user_message)
        
        # Try to execute reproduction
        reproduction_result = {
            "agent": self.name,
            "reproduction_info": reproduction_info,
            "status": "completed"
        }
        
        # TODO: Actually run the reproduction code
        # result = self.code_executor.execute(reproduction_code)
        # reproduction_result["execution_result"] = result
        
        return reproduction_result
    