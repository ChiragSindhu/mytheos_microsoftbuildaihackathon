"""Root Cause Agent - Identifies the root cause."""
from typing import Dict, Any
from src.core.agent_base import BaseAgent

class RootCauseAgent(BaseAgent):
    """Agent responsible for root cause analysis."""
    
    def __init__(self, **kwargs):
        super().__init__(name="RootCause", temperature=0.3, **kwargs)
    
    def get_system_prompt(self) -> str:
        return """You are an expert at root cause analysis. Your role is to:

1. Analyze all gathered information
2. Trace the error to its source
3. Identify the root cause (not just symptoms)
4. Explain the causal chain
5. Assess impact and severity

Be precise and thorough. Output structured analysis in JSON format with:
- root_cause: Clear description
- causal_chain: Step-by-step how bug occurs
- affected_files: List of files
- severity: critical|high|medium|low
- impact: Description of impact"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Identify root cause."""
        user_message = f"""
Plan:
{context.get('plan', '')}

Reproduction Results:
{context.get('reproduction_info', '')}

Code Analysis:
{context.get('code_analysis', '')}

Historical Context:
{context.get('context_info', '')}

Identify the root cause of this bug.
"""
        
        root_cause_analysis = self.generate(user_message)
        
        return {
            "agent": self.name,
            "root_cause_analysis": root_cause_analysis,
            "status": "completed"
        }