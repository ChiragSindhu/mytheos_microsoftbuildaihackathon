"""Code Analysis Agent - Analyzes code structure and data flow."""
from typing import Dict, Any, List
from src.core.agent_base import BaseAgent
from src.tools.ast_analyzer import ASTAnalyzer

class CodeAnalysisAgent(BaseAgent):
    """Agent responsible for code analysis."""
    
    def __init__(self, **kwargs):
        super().__init__(name="CodeAnalysis", temperature=0.3, **kwargs)
        self.ast_analyzer = ASTAnalyzer()
    
    def get_system_prompt(self) -> str:
        return """You are an expert code analyst. Your role is to:

1. Analyze code structure and patterns
2. Build call graphs and data flow
3. Identify suspicious code locations
4. Find related functions and dependencies
5. Detect code smells and anti-patterns

Output structured analysis in JSON:
- suspicious_locations: List of potentially buggy code locations
- call_graph: Function call relationships
- data_flow: Variable/data flow analysis
- dependencies: Related modules/functions
- code_smells: Detected issues"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code structure."""
        
        # Extract file locations from plan
        files_to_analyze = self._extract_files(context)
        
        user_message = f"""
Debugging Plan:
{context.get('plan', '')}

Error Log:
{context.get('error_log', '')}

Files to Analyze:
{files_to_analyze}

Code Content:
{context.get('relevant_code', '')}

Analyze this code for:
1. Call paths that could lead to the error
2. Data flow issues
3. Suspicious patterns
4. Dependencies that might be involved
"""
        
        code_analysis = self.generate(user_message)
        
        return {
            "agent": self.name,
            "code_analysis": code_analysis,
            "analyzed_files": files_to_analyze,
            "status": "completed"
        }
    
    def _extract_files(self, context: Dict[str, Any]) -> List[str]:
        """Extract relevant files from context."""
        # This would parse the plan and extract file paths
        return context.get('files', [])