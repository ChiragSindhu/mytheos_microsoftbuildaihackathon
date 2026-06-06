"""Test execution and verification."""
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TestRunner:
    """Run tests and analyze results."""
    
    def __init__(self):
        self.supported_frameworks = {
            'python': ['pytest', 'unittest'],
            'javascript': ['jest', 'mocha'],
            'java': ['junit']
        }
    
    def run_pytest(self, test_path: str) -> Dict[str, Any]:
        """Run pytest tests."""
        try:
            result = subprocess.run(
                ['pytest', test_path, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "passed": self._count_passed(result.stdout),
                "failed": self._count_failed(result.stdout)
            }
        except Exception as e:
            logger.error(f"Test execution error: {e}")
            return {
                "status": "error",
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    def _count_passed(self, output: str) -> int:
        """Count passed tests from output."""
        import re
        match = re.search(r'(\d+) passed', output)
        return int(match.group(1)) if match else 0
    
    def _count_failed(self, output: str) -> int:
        """Count failed tests from output."""
        import re
        match = re.search(r'(\d+) failed', output)
        return int(match.group(1)) if match else 0