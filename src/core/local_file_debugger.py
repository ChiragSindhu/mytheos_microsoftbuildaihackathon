"""Debug local Python files.

Accepts a ProgressEmitter for progress reporting.
Has zero knowledge of SSE, WebSockets, or any transport.

Agent pipeline (sequential, mirrors MYTHEOSOrchestrator):
    1. Planner        – strategy from file content + error log
    2. Reproduction   – analyse the captured execution failure
    3. Code Analysis  – structure, deps, execution flow
    4. Context        – local file history / test suite context
    5. Root Cause     – validate the most probable failure cause
    6. Fix            – targeted code modification / remediation
    7. Test           – regression tests + fix validation
    8. Review         – quality, security, maintainability gate
"""
from __future__ import annotations

import asyncio
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

from src.agents.code_analysis import CodeAnalysisAgent
from src.agents.context import ContextAgent
from src.agents.fix import FixAgent
from src.agents.planner import PlannerAgent
from src.agents.reproduction import ReproductionAgent
from src.agents.review import ReviewAgent
from src.agents.root_cause import RootCauseAgent
from src.agents.test import TestAgent
from src.core.progress_emitter import ProgressEmitter
from src.utils.logger import get_logger
from src.utils.parsers import parse_error_log

logger = get_logger(__name__)
console = Console()


class LocalFileDebugger:
    """
    Debug local Python files using the full 8-agent sequential pipeline.

    Args:
        verbose:  Echo rich console output (useful in CLI mode).
        emitter:  Optional ProgressEmitter. When provided, real-time phase
                  events are emitted as each step runs. When omitted the
                  debugger works in silent/CLI mode.
    """

    # Phase names — kept identical to MYTHEOSOrchestrator so SSE consumers
    # need only one event-handling path regardless of which debugger is used.
    PHASE_INIT          = "initialization"
    PHASE_PLANNING      = "planning"
    PHASE_REPRODUCTION  = "reproduction"
    PHASE_CODE_ANALYSIS = "code_analysis"
    PHASE_CONTEXT       = "context"
    PHASE_ROOT_CAUSE    = "root_cause"
    PHASE_FIX           = "fix"
    PHASE_TEST          = "test"
    PHASE_REVIEW        = "review"
    PHASE_OUTPUT        = "output"

    def __init__(
        self,
        verbose: bool = False,
        emitter: Optional[ProgressEmitter] = None,
    ) -> None:
        self.verbose = verbose
        self.emitter = emitter
        self.agents: Dict[str, Any] = {
            "planner":       PlannerAgent(),
            "reproduction":  ReproductionAgent(),
            "code_analysis": CodeAnalysisAgent(),
            "context":       ContextAgent(),
            "root_cause":    RootCauseAgent(),
            "fix":           FixAgent(),
            "test":          TestAgent(),
            "review":        ReviewAgent(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _emit(
        self,
        phase: str,
        message: str,
        *,
        done: bool = False,
        **extra: Any,
    ) -> None:
        """Emit a progress event. No-ops when no emitter is attached."""
        if self.emitter:
            await self.emitter.emit(phase, message, done=done, **extra)

    async def _run_agent(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single agent via asyncio.to_thread and merge its result into context."""
        result: Dict[str, Any] = await asyncio.to_thread(
            self.agents[name].process, context
        )
        context.update(result)
        return result

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
        Debug a local Python file through the complete 8-agent pipeline.

        Args:
            file_path: Path to the Python file to debug.
            auto_run:  Execute the file before analysis to capture runtime errors.
            test_file: Optional pytest file to run during the Test phase.

        Returns:
            Debug report containing execution output, per-agent analysis, and status.
        """
        path = Path(file_path)

        if not path.exists():
            return {"error": f"File not found: {path}"}

        with open(path, "r", encoding="utf-8") as fh:
            code_content = fh.read()

        # ── PHASE 0: initialisation ──────────────────────────────────────
        await self._emit(self.PHASE_INIT, f"Loading file: {path.name}...")

        # Shared context dict — every agent reads and extends this.
        context: Dict[str, Any] = {
            "file_path":    str(path),
            "repo_path":    str(path.parent),
            "code_content": code_content,
            "language":     "python",
            "error_log":    "",
            "execution_output": "",
        }

        result: Dict[str, Any] = {
            "file_path":       str(path),
            "code_content":    code_content,
            "errors_found":    False,
            "execution_error": None,
            "output":          None,
            "analysis":        {},
        }

        await self._emit(self.PHASE_INIT, "File loaded.", done=True)

        # ── PHASE 1: planner ─────────────────────────────────────────────
        # Run the Planner first — even before execution — so every downstream
        # agent gets a strategy to work from.
        console.print("\n[bold cyan] PHASE 1: Planning[/bold cyan]")
        await self._emit(
            self.PHASE_PLANNING,
            "Planner agent building a debugging strategy from the file content...",
        )

        plan_result = await self._run_agent("planner", context)
        plan = plan_result.get("plan", "")

        if not plan:
            logger.warning("Planner returned an empty plan — downstream agents may have reduced context.")

        console.print(f"   Plan ready: {len(plan)} chars")
        await self._emit(
            self.PHASE_PLANNING,
            "Debugging plan created.",
            done=True,
            plan=plan,
        )

        # ── PHASE 2: reproduction ────────────────────────────────────────
        # Sub-step 2a: actually execute the file to capture a real error log.
        console.print("\n[bold magenta] PHASE 2: Reproduction[/bold magenta]")
        await self._emit(
            self.PHASE_REPRODUCTION,
            "Running file to capture execution behaviour...",
        )

        if auto_run:
            execution = await asyncio.to_thread(self._run_file, path)
            result["output"]          = execution["output"]
            result["execution_error"] = execution["error"]
            context["execution_output"] = execution["output"] or ""
            context["error_log"]        = execution["error"]  or ""

            if execution["status"] == "error":
                result["errors_found"] = True
                if self.verbose:
                    console.print("[red] Execution error detected[/red]")
                    console.print(f"\n[dim]{execution['error'][:500]}[/dim]")

                # Parse the error log and enrich context so agents get
                # structured error fields (type, message, line, function).
                if context["error_log"]:
                    parsed = parse_error_log(context["error_log"])
                    context["parsed_error"] = {
                        "error_type":    parsed.error_type,
                        "error_message": parsed.error_message,
                        "file_path":     parsed.file_path,
                        "line_number":   parsed.line_number,
                        "function_name": parsed.function_name,
                    }
                    if self.verbose:
                        console.print(f"  [red]Error Type:[/red] {parsed.error_type}")
                        console.print(f"  [red]Message:[/red]    {parsed.error_message}")
                        if parsed.line_number:
                            console.print(f"  [red]Line:[/red]       {parsed.line_number}")
            else:
                if self.verbose:
                    console.print("[green] File executed successfully[/green]")

        # Sub-step 2b: Reproduction agent analyses the captured execution data.
        repro_result = await self._run_agent("reproduction", context)
        reproduction_info = repro_result.get("reproduction_info", "")

        console.print("   Reproduction Agent: Complete")
        await self._emit(
            self.PHASE_REPRODUCTION,
            "Execution captured and reproduction analysis complete.",
            done=True,
            errors_found=result["errors_found"],
            execution_error=result["execution_error"],
            output=result["output"],
            reproduction=reproduction_info,
        )

        # ── PHASE 3: code analysis ───────────────────────────────────────
        console.print("\n[bold blue] PHASE 3: Code Analysis[/bold blue]")
        await self._emit(
            self.PHASE_CODE_ANALYSIS,
            "Code analysis agent examining structure, dependencies, and execution flow...",
        )

        code_result = await self._run_agent("code_analysis", context)
        code_analysis = code_result.get("code_analysis", "")

        console.print("   Code Analysis Agent: Complete")
        await self._emit(
            self.PHASE_CODE_ANALYSIS,
            "Code structure and flow analysis complete.",
            done=True,
            code_analysis=code_analysis,
        )

        # ── PHASE 4: context ─────────────────────────────────────────────
        console.print("\n[bold white] PHASE 4: Context Gathering[/bold white]")
        await self._emit(
            self.PHASE_CONTEXT,
            "Context agent retrieving local file history, related modules, "
            "and test suite context...",
        )

        ctx_result = await self._run_agent("context", context)
        context_info = ctx_result.get("context_info", "")

        console.print("   Context Agent: Complete")
        await self._emit(
            self.PHASE_CONTEXT,
            "File context gathered.",
            done=True,
            context_info=context_info,
        )

        # ── PHASE 5: root cause ───────────────────────────────────────────
        console.print("\n[bold red] PHASE 5: Root Cause Analysis[/bold red]")
        await self._emit(
            self.PHASE_ROOT_CAUSE,
            "Root cause agent synthesising reproduction, code, and context "
            "findings to identify the most probable failure source...",
        )

        root_result = await self._run_agent("root_cause", context)
        root_cause = root_result.get("root_cause_analysis", "")

        console.print("   Root Cause Agent: Complete")
        await self._emit(
            self.PHASE_ROOT_CAUSE,
            "Root cause identified and validated.",
            done=True,
            root_cause=root_cause,
        )

        # ── PHASE 6: fix ──────────────────────────────────────────────────
        console.print("\n[bold green]🔧 PHASE 6: Fix Generation[/bold green]")
        await self._emit(
            self.PHASE_FIX,
            "Fix agent generating targeted code modifications based on the "
            "confirmed root cause...",
        )

        fix_result = await self._run_agent("fix", context)
        fix_proposal = fix_result.get("fix_proposal", "")

        console.print("   Fix Agent: Complete")
        await self._emit(
            self.PHASE_FIX,
            "Fix proposal generated.",
            done=True,
            fix=fix_proposal,
        )

        # ── PHASE 7: test ─────────────────────────────────────────────────
        console.print("\n[bold blue] PHASE 7: Test Generation[/bold blue]")
        await self._emit(
            self.PHASE_TEST,
            "Test agent creating regression tests and validating the proposed fix...",
        )

        # Sub-step 7a: run any existing test file first so results go into context.
        if test_file:
            await self._emit(self.PHASE_TEST, f"Running existing test suite: {test_file}...")
            test_run = await asyncio.to_thread(self._run_tests, test_file)
            result["test_output"] = test_run
            context["test_run_output"] = test_run

            if test_run["status"] == "error" or test_run.get("failed", 0) > 0:
                result["errors_found"] = True

            console.print(
                f"   Test run: {test_run.get('passed', 0)} passed, "
                f"{test_run.get('failed', 0)} failed"
            )

        # Sub-step 7b: Test agent generates new regression tests.
        test_result = await self._run_agent("test", context)
        test_code = test_result.get("test_code", "")

        console.print("   Test Agent: Complete")
        await self._emit(
            self.PHASE_TEST,
            "Regression tests generated and fix validated.",
            done=True,
            tests=test_code,
            **(
                {
                    "passed": result.get("test_output", {}).get("passed", 0),
                    "failed": result.get("test_output", {}).get("failed", 0),
                }
                if test_file else {}
            ),
        )

        # ── PHASE 8: review ───────────────────────────────────────────────
        console.print("\n[bold yellow] PHASE 8: Code Review[/bold yellow]")
        await self._emit(
            self.PHASE_REVIEW,
            "Review agent performing quality, security, and maintainability "
            "checks on the fix and test suite...",
        )

        review_result = await self._run_agent("review", context)
        review = review_result.get("review_result", "")

        console.print("   Review Agent: Complete")
        await self._emit(
            self.PHASE_REVIEW,
            "Review complete.",
            done=True,
            review=review,
        )

        # ── PHASE 9: output ───────────────────────────────────────────────
        console.print("\n[bold green] PHASE 9: Generating Output[/bold green]")
        await self._emit(self.PHASE_OUTPUT, "Assembling debug report...")

        result["analysis"] = {
            # Keys mirror the SSE payload keys for each phase
            "plan":          context.get("plan"),
            "reproduction":  context.get("reproduction_info"),
            "code_analysis": context.get("code_analysis"),
            "context_info":  context.get("context_info"),
            "root_cause":    context.get("root_cause_analysis"),
            "fix":           context.get("fix_proposal"),
            "tests":         context.get("test_code"),
            "review":        context.get("review_result"),
        }

        await self._emit(self.PHASE_OUTPUT, "Debug report ready.", done=True)
        return result

    # ------------------------------------------------------------------
    # Subprocess helpers (sync — called via asyncio.to_thread)
    # ------------------------------------------------------------------

    def _run_file(self, file_path: Path) -> Dict[str, Any]:
        """Execute the target file and return status, stdout, and stderr."""
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
            return {
                "status": "timeout",
                "output": "",
                "error": "Execution timed out after 30 seconds",
            }
        except Exception as exc:
            return {"status": "error", "output": "", "error": str(exc)}

    def _run_tests(self, test_file: str) -> Dict[str, Any]:
        """Run pytest against test_file and return pass/fail counts."""
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
                "error":  proc.stderr,
                "passed": self._count_tests(proc.stdout, "passed"),
                "failed": self._count_tests(proc.stdout, "failed"),
            }
        except Exception as exc:
            return {"status": "error", "output": "", "error": str(exc)}

    @staticmethod
    def _count_tests(output: str, status: str) -> int:
        match = re.search(rf"(\d+) {status}", output)
        return int(match.group(1)) if match else 0
    