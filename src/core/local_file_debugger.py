"""Debug local Python files."""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from src.core.agent_base import BaseAgent
from src.agents.planner import PlannerAgent
from src.agents.code_analysis import CodeAnalysisAgent
from src.agents.root_cause import RootCauseAgent
from src.agents.fix import FixAgent
from src.agents.test import TestAgent
from src.utils.logger import get_logger
from src.utils.parsers import parse_error_log
import json

logger = get_logger(__name__)
console = Console()

class LocalFileDebugger:
    """Debug local Python files."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.agents = {
            "planner": PlannerAgent(),
            "code_analysis": CodeAnalysisAgent(),
            "root_cause": RootCauseAgent(),
            "fix": FixAgent(),
            "test": TestAgent(),
        }
    
    async def debug_file(
        self,
        file_path: str,
        auto_run: bool = True,
        test_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Debug a local Python file.
        
        Args:
            file_path: Path to Python file
            auto_run: Automatically run file to detect errors
            test_file: Optional test file to run
        
        Returns:
            Debug report with errors, analysis, and fixes
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        result = {
            "file_path": str(file_path),
            "code_content": code_content,
            "errors_found": False,
            "execution_error": None,
            "output": None,
            "analysis": {}
        }
        
        # Step 1: Run the file to detect errors
        if auto_run:
            console.print("[yellow]  Running file to detect errors...[/yellow]")
            execution_result = self._run_file(file_path)
            
            result["output"] = execution_result["output"]
            result["execution_error"] = execution_result["error"]
            
            if execution_result["status"] == "error":
                result["errors_found"] = True
                console.print("[red] Error detected during execution[/red]")
                
                if self.verbose:
                    console.print(f"\n[dim]{execution_result['error'][:500]}[/dim]")
            else:
                console.print("[green] File executed successfully[/green]")
        
        # Step 2: Run tests if provided
        if test_file:
            console.print(f"[yellow] Running tests: {test_file}[/yellow]")
            test_result = self._run_tests(test_file)
            result["test_output"] = test_result
            
            if test_result["status"] == "error" or test_result.get("failed", 0) > 0:
                result["errors_found"] = True
        
        # Step 3: If errors found, run analysis
        if result["errors_found"] or not auto_run:
            console.print("\n[cyan] Analyzing code...[/cyan]")
            analysis = await self._analyze_and_fix(
                code_content=code_content,
                file_path=str(file_path),
                error_log=result["execution_error"] or "",
                test_output=result.get("test_output", {})
            )
            result["analysis"] = analysis
        
        return result
    
    def _run_file(self, file_path: Path) -> Dict[str, Any]:
        """Run Python file and capture output/errors."""
        try:
            result = subprocess.run(
                [sys.executable, str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=file_path.parent
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "output": result.stdout,
                    "error": None
                }
            else:
                return {
                    "status": "error",
                    "output": result.stdout,
                    "error": result.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "output": "",
                "error": "Execution timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }
    
    def _run_tests(self, test_file: str) -> Dict[str, Any]:
        """Run pytest on test file."""
        try:
            result = subprocess.run(
                ['pytest', test_file, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr,
                "passed": self._count_tests(result.stdout, "passed"),
                "failed": self._count_tests(result.stdout, "failed")
            }
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }
    
    def _count_tests(self, output: str, status: str) -> int:
        """Count test results."""
        import re
        match = re.search(rf'(\d+) {status}', output)
        return int(match.group(1)) if match else 0
    
    async def _analyze_and_fix(
        self,
        code_content: str,
        file_path: str,
        error_log: str,
        test_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run agent analysis to find root cause and generate fix."""
        
        context = {
            "file_path": file_path,
            "code_content": code_content,
            "error_log": error_log,
            "test_output": test_output,
            "language": "python"
        }
        
        # Parse error if available
        if error_log:
            parsed_error = parse_error_log(error_log)
            context["parsed_error"] = {
                "error_type": parsed_error.error_type,
                "error_message": parsed_error.error_message,
                "file_path": parsed_error.file_path,
                "line_number": parsed_error.line_number,
                "function_name": parsed_error.function_name
            }
            
            console.print(f"  [red]Error Type:[/red] {parsed_error.error_type}")
            console.print(f"  [red]Message:[/red] {parsed_error.error_message}")
            if parsed_error.line_number:
                console.print(f"  [red]Line:[/red] {parsed_error.line_number}")
        
        analysis = {}
        
        # Code Analysis
        console.print("  [cyan]→ Code Analysis Agent[/cyan]")
        code_analysis_result = self.agents["code_analysis"].process(context)
        context.update(code_analysis_result)
        analysis["code_analysis"] = code_analysis_result.get("code_analysis", "")
        
        # Root Cause
        console.print("  [cyan]→ Root Cause Agent[/cyan]")
        root_cause_result = self.agents["root_cause"].process(context)
        context.update(root_cause_result)
        analysis["root_cause"] = root_cause_result.get("root_cause_analysis", "")
        
        # Fix
        console.print("  [cyan]→ Fix Agent[/cyan]")
        fix_result = self.agents["fix"].process(context)
        context.update(fix_result)
        analysis["fix"] = fix_result.get("fix_proposal", "")
        
        # Tests
        console.print("  [cyan]→ Test Agent[/cyan]")
        test_result = self.agents["test"].process(context)
        analysis["tests"] = test_result.get("test_code", "")
        
        return analysis