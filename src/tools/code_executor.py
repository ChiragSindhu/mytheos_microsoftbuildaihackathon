"""Safe code execution environment."""
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CodeExecutor:
    """Execute code safely in isolated environment."""
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.enabled = settings.ENABLE_CODE_EXECUTION
    
    def execute_python(self, code: str, test_mode: bool = False) -> Dict[str, Any]:
        """Execute Python code."""
        if not self.enabled:
            return {"status": "disabled", "output": "Code execution is disabled"}
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Clean up
            Path(temp_file).unlink()
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": f"Execution timed out after {self.timeout} seconds",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    def execute_javascript(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js."""
        if not self.enabled:
            return {"status": "disabled", "output": "Code execution is disabled"}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            Path(temp_file).unlink()
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "return_code": -1
            }