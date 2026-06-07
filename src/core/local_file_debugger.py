"""Debug local Python files.

Accepts a ProgressEmitter for progress reporting.
Has zero knowledge of SSE, WebSockets, or any transport.
"""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

from src.agents.code_analysis import CodeAnalysisAgent
from src.agents.fix import FixAgent
from src.agents.planner import PlannerAgent
from src.agents.root_cause import RootCauseAgent
from src.agents.test import TestAgent
from src.core.agent_base import BaseAgent
from src.core.progress_emitter import ProgressEmitter
from src.utils.logger import get_logger
from src.utils.parsers import parse_error_log

logger = get_logger(__name__)
console = Console()


class LocalFileDebugger:
    """
    Debug local Python files.

    Args:
        verbose:  Echo rich console output (useful in CLI mode).
        emitter:  Optional ProgressEmitter. When provided, real-time phase
                  events are emitted as each step runs. When omitted the
                  debugger works in silent/CLI mode.
    """

    def __init__(
        self,
        verbose: bool = False,
        emitter: Optional[ProgressEmitter] = None,
    ):
        self.verbose = verbose
        self.emitter = emitter
        self.agents = {
            "planner": PlannerAgent(),
            "code_analysis": CodeAnalysisAgent(),
            "root_cause": RootCauseAgent(),
            "fix": FixAgent(),
            "test": TestAgent(),
        }

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    async def _emit(self, phase: str, message: str, *, done: bool = False, **extra: Any) -> None:
        if self.emitter:
            await self.emitter.emit(phase, message, done=done, **extra)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def debug_file(
        self,
        file_path: str,
        auto_run: bool = True,
        test_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Debug a local Python file.

        Args:
            file_path: Path to the Python file to debug.
            auto_run:  Automatically run the file to detect runtime errors.
            test_file: Optional pytest file to run.

        Returns:
            Debug report: errors, execution output, and agent analysis.
        """
        path = Path(file_path)

        if not path.exists():
            return {"error": f"File not found: {path}"}

        with open(path, "r", encoding="utf-8") as f:
            code_content = f.read()

        result: Dict[str, Any] = {
            "file_path": str(path),
            "code_content": code_content,
            "errors_found": False,
            "execution_error": None,
            "output": None,
            "analysis": {},
        }

        # ── Step 1: execute file ──────────────────────────────────────────
        if auto_run:
            await self._emit("reproduction", "Running file to detect runtime errors...")

            execution_result = await asyncio.to_thread(self._run_file, path)
            result["output"] = execution_result["output"]
            result["execution_error"] = execution_result["error"]

            if execution_result["status"] == "error":
                result["errors_found"] = True
                if self.verbose:
                    console.print("[red] Error detected during execution[/red]")
                    console.print(f"\n[dim]{execution_result['error'][:500]}[/dim]")

                await self._emit(
                    "reproduction",
                    "Execution error detected.",
                    done=True,
                    errors_found=True,
                    execution_error=execution_result["error"],
                    output=execution_result["output"],
                )
            else:
                if self.verbose:
                    console.print("[green] File executed successfully[/green]")

                await self._emit(
                    "reproduction",
                    "File executed successfully — no runtime errors.",
                    done=True,
                    errors_found=False,
                    output=execution_result["output"],
                )

        # ── Step 2: run tests ─────────────────────────────────────────────
        if test_file:
            await self._emit("test_run", f"Running tests: {test_file}...")

            test_run_result = await asyncio.to_thread(self._run_tests, test_file)
            result["test_output"] = test_run_result

            if test_run_result["status"] == "error" or test_run_result.get("failed", 0) > 0:
                result["errors_found"] = True

            await self._emit(
                "test_run",
                f"Tests complete: {test_run_result.get('passed', 0)} passed, "
                f"{test_run_result.get('failed', 0)} failed.",
                done=True,
                **test_run_result,
            )

        # ── Step 3: agent analysis ────────────────────────────────────────
        if result["errors_found"] or not auto_run:
            analysis = await self._analyze_and_fix(
                code_content=code_content,
                file_path=str(path),
                error_log=result["execution_error"] or "",
                test_output=result.get("test_output", {}),
            )
            result["analysis"] = analysis

        return result

    # ------------------------------------------------------------------
    # Agent pipeline (each step emits its own events)
    # ------------------------------------------------------------------

    async def _analyze_and_fix(
        self,
        code_content: str,
        file_path: str,
        error_log: str,
        test_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "file_path": file_path,
            "code_content": code_content,
            "error_log": error_log,
            "test_output": test_output,
            "language": "python",
        }

        if error_log:
            parsed = parse_error_log(error_log)
            context["parsed_error"] = {
                "error_type": parsed.error_type,
                "error_message": parsed.error_message,
                "file_path": parsed.file_path,
                "line_number": parsed.line_number,
                "function_name": parsed.function_name,
            }
            if self.verbose:
                console.print(f"  [red]Error Type:[/red] {parsed.error_type}")
                console.print(f"  [red]Message:[/red] {parsed.error_message}")
                if parsed.line_number:
                    console.print(f"  [red]Line:[/red] {parsed.line_number}")

        analysis: Dict[str, Any] = {}

        # Code analysis
        await self._emit("analysis", "Code analysis agent examining structure and patterns...")
        code_result = await asyncio.to_thread(self.agents["code_analysis"].process, context)
        context.update(code_result)
        analysis["code_analysis"] = code_result.get("code_analysis", "")
        await self._emit("analysis", "Code analysis complete.", done=True,
                         code_analysis=analysis["code_analysis"])

        # Root cause
        await self._emit("root_cause", "Root cause agent identifying source of issue...")
        root_result = await asyncio.to_thread(self.agents["root_cause"].process, context)
        context.update(root_result)
        analysis["root_cause"] = root_result.get("root_cause_analysis", "")
        await self._emit("root_cause", "Root cause identified.", done=True,
                         root_cause=analysis["root_cause"])

        # Fix
        await self._emit("fix", "Fix agent generating recommendations...")
        fix_result = await asyncio.to_thread(self.agents["fix"].process, context)
        context.update(fix_result)
        analysis["fix"] = fix_result.get("fix_proposal", "")
        await self._emit("fix", "Fix generated.", done=True, fix=analysis["fix"])

        # Tests
        await self._emit("test", "Test agent creating test cases...")
        test_result = await asyncio.to_thread(self.agents["test"].process, context)
        analysis["tests"] = test_result.get("test_code", "")
        await self._emit("test", "Tests generated.", done=True,
                         tests=analysis["tests"])

        return analysis

    # ------------------------------------------------------------------
    # Subprocess helpers (sync — called via asyncio.to_thread)
    # ------------------------------------------------------------------

    def _run_file(self, file_path: Path) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                [sys.executable, str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=file_path.parent,
            )
            if proc.returncode == 0:
                return {"status": "success", "output": proc.stdout, "error": None}
            return {"status": "error", "output": proc.stdout, "error": proc.stderr}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "output": "", "error": "Execution timed out after 30 seconds"}
        except Exception as e:
            return {"status": "error", "output": "", "error": str(e)}

    def _run_tests(self, test_file: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                ["pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "status": "success" if proc.returncode == 0 else "error",
                "output": proc.stdout,
                "error": proc.stderr,
                "passed": self._count_tests(proc.stdout, "passed"),
                "failed": self._count_tests(proc.stdout, "failed"),
            }
        except Exception as e:
            return {"status": "error", "output": "", "error": str(e)}

    def _count_tests(self, output: str, status: str) -> int:
        match = re.search(rf"(\d+) {status}", output)
        return int(match.group(1)) if match else 0
    