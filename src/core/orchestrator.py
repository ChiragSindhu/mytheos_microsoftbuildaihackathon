"""Main orchestrator for the debugging swarm.

Accepts a ProgressEmitter for progress reporting.
Has zero knowledge of SSE, WebSockets, or any transport.

Agent pipeline (sequential):
    1. Planner        – strategy from repo + error + issue
    2. Reproduction   – reproduce the failing execution path
    3. Code Analysis  – structure, deps, execution flow
    4. Context        – commits, PRs, docs, related issues
    5. Root Cause     – validate the most probable failure cause
    6. Fix            – targeted code modification / remediation
    7. Test           – regression tests + fix validation
    8. Review         – quality, security, maintainability gate
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

from rich.console import Console
from rich.tree import Tree

from src.agents.code_analysis import CodeAnalysisAgent
from src.agents.context import ContextAgent
from src.agents.fix import FixAgent
from src.agents.planner import PlannerAgent
from src.agents.reproduction import ReproductionAgent
from src.agents.review import ReviewAgent
from src.agents.root_cause import RootCauseAgent
from src.agents.test import TestAgent
from src.core.progress_emitter import ProgressEmitter
from src.core.state import SwarmState
from src.utils.formatters import format_bug_report, format_pull_request
from src.utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


class MYTHEOSOrchestrator:
    """
    Orchestrates the full debugging swarm in a strict sequential pipeline.

    Every agent runs in dependency order so that each step's output is
    available as context for every subsequent step.

    Args:
        emitter: Optional ProgressEmitter. When provided, real-time phase
                 events are emitted as each agent runs. When omitted the
                 orchestrator works in silent/CLI mode.
    """

    # Phase names used for SSE events — kept as class constants so
    # consumers can reference them without hard-coding strings.
    PHASE_INIT         = "initialization"
    PHASE_PLANNING     = "planning"
    PHASE_REPRODUCTION = "reproduction"
    PHASE_CODE_ANALYSIS = "code_analysis"
    PHASE_CONTEXT      = "context"
    PHASE_ROOT_CAUSE   = "root_cause"
    PHASE_FIX          = "fix"
    PHASE_TEST         = "test"
    PHASE_REVIEW       = "review"
    PHASE_OUTPUT       = "output"

    def __init__(self, emitter: Optional[ProgressEmitter] = None) -> None:
        self.state   = SwarmState()
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
        self.context: Dict[str, Any] = {}

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

    async def _run_agent(self, name: str) -> Dict[str, Any]:
        """Run a single agent via asyncio.to_thread and return its result dict."""
        result: Dict[str, Any] = await asyncio.to_thread(
            self.agents[name].process, self.context
        )
        self.context.update(result)
        return result

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def print_flow_diagram(self) -> None:
        """Print the sequential agent pipeline to the console."""
        tree = Tree(" [bold blue]MYTHEOS Sequential Flow[/bold blue]")
        node = tree.add(" [yellow]GitHub Repo + Error Logs[/yellow]")
        steps = [
            (" [cyan]1. Planner Agent[/cyan]",        "Strategy & debugging plan"),
            (" [magenta]2. Reproduction Agent[/magenta]", "Failing execution paths"),
            (" [blue]3. Code Analysis Agent[/blue]",   "Structure, deps, flow"),
            (" [white]4. Context Agent[/white]",        "Commits, PRs, docs, issues"),
            (" [red]5. Root Cause Agent[/red]",         "Identify & validate root cause"),
            ("🔧 [green]6. Fix Agent[/green]",          "Code modifications & remediation"),
            (" [blue]7. Test Agent[/blue]",             "Regression tests & fix validation"),
            (" [yellow]8. Review Agent[/yellow]",       "Quality, security, maintainability"),
        ]
        for label, description in steps:
            node = node.add(f"{label}  [dim]{description}[/dim]")
        console.print(tree)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def debug(
        self,
        repo_url: str,
        error_log: str,
        repo_path: Optional[str] = None,
        issue_id: Optional[str] = None,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        Run the complete sequential debugging pipeline, emitting SSE progress
        events at every phase boundary.

        Args:
            repo_url:   Remote URL of the repository being debugged.
            error_log:  Raw error / stack-trace text.
            repo_path:  Optional local path to a cloned repo (adds source context).
            issue_id:   Optional issue / ticket identifier for the Context agent.
            language:   Primary language of the target codebase.

        Returns:
            A dict containing bug_report, pull_request, per-agent context, and status.
        """
        logger.info("Starting debug process for %s", repo_url)
        self.print_flow_diagram()

        # ── PHASE 0: initialisation ──────────────────────────────────────
        await self._emit(self.PHASE_INIT, "Preparing repository context...")

        self.context = {
            "repo_url":   repo_url,
            "repo_path":  repo_path,
            "error_log":  error_log,
            "issue_id":   issue_id,
            "language":   language,
            "repo_name":  repo_url.rstrip("/").split("/")[-1],
        }

        if repo_path:
            self.context["relevant_code"]  = self._load_relevant_code(repo_path, error_log)
            self.context["repo_structure"] = self._get_repo_structure(repo_path)

        await self._emit(self.PHASE_INIT, "Repository context ready.", done=True)

        # ── PHASE 1: planner ─────────────────────────────────────────────
        # The Planner is the backbone of the pipeline: every downstream agent
        # reads context["plan"] to scope its work.
        console.print("\n[bold cyan] PHASE 1: Planning[/bold cyan]")
        await self._emit(
            self.PHASE_PLANNING,
            "Planner agent analysing repo, issue, and error log to create a "
            "structured debugging strategy...",
        )

        plan_result = await self._run_agent("planner")
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
        console.print("\n[bold magenta] PHASE 2: Reproduction[/bold magenta]")
        await self._emit(
            self.PHASE_REPRODUCTION,
            "Reproduction agent tracing failing execution paths guided by the plan...",
        )

        repro_result = await self._run_agent("reproduction")
        reproduction_info = repro_result.get("reproduction_info", "")

        console.print("   Reproduction Agent: Complete")
        await self._emit(
            self.PHASE_REPRODUCTION,
            "Failing execution path reproduced.",
            done=True,
            reproduction=reproduction_info,
        )

        # ── PHASE 3: code analysis ───────────────────────────────────────
        console.print("\n[bold blue] PHASE 3: Code Analysis[/bold blue]")
        await self._emit(
            self.PHASE_CODE_ANALYSIS,
            "Code analysis agent examining structure, dependencies, and execution flow...",
        )

        code_result = await self._run_agent("code_analysis")
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
            "Context agent retrieving commit history, pull requests, "
            "documentation, and related issues...",
        )

        ctx_result = await self._run_agent("context")
        context_info = ctx_result.get("context_info", "")

        console.print("   Context Agent: Complete")
        await self._emit(
            self.PHASE_CONTEXT,
            "Historical and contextual information gathered.",
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

        root_result = await self._run_agent("root_cause")
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

        fix_result = await self._run_agent("fix")
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

        test_result = await self._run_agent("test")
        test_code = test_result.get("test_code", "")

        console.print("   Test Agent: Complete")
        await self._emit(
            self.PHASE_TEST,
            "Regression tests generated and fix validated.",
            done=True,
            tests=test_code,
        )

        # ── PHASE 8: review ───────────────────────────────────────────────
        console.print("\n[bold yellow] PHASE 8: Code Review[/bold yellow]")
        await self._emit(
            self.PHASE_REVIEW,
            "Review agent performing quality, security, and maintainability "
            "checks on the fix and test suite...",
        )

        review_result = await self._run_agent("review")
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
        await self._emit(self.PHASE_OUTPUT, "Generating bug report and pull request...")

        output = self._generate_output(self.context)

        await self._emit(self.PHASE_OUTPUT, "Output ready.", done=True)
        logger.info("Debug process complete for %s", repo_url)

        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_relevant_code(self, repo_path: str, error_log: str) -> str:
        """Walk the repo and return the first five source files as a single string."""
        code_snippets: list[str] = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [
                d for d in dirs
                if d not in {".git", "__pycache__", "node_modules", "venv"}
            ]
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            relative = os.path.relpath(file_path, repo_path)
                            code_snippets.append(f"\n--- {relative} ---\n{f.read()}")
                    except Exception as exc:
                        logger.warning("Could not read %s: %s", file_path, exc)
        return "\n".join(code_snippets[:5])

    def _get_repo_structure(self, repo_path: str) -> str:
        """Return a tree-style string of the repo's directory layout (max 50 lines)."""
        structure: list[str] = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [
                d for d in dirs
                if d not in {".git", "__pycache__", "node_modules", "venv"}
            ]
            level = root.replace(repo_path, "").count(os.sep)
            structure.append(f"{'  ' * level}{os.path.basename(root)}/")
            for file in files:
                structure.append(f"{'  ' * (level + 1)}{file}")
        return "\n".join(structure[:50])

    def _generate_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble the final output dict from the fully-populated context."""
        return {
            "bug_report":   format_bug_report(context),
            "pull_request": format_pull_request(context),
            "context": {
                # Each key mirrors the SSE payload key for the corresponding phase
                "plan":         context.get("plan"),
                "reproduction": context.get("reproduction_info"),
                "code_analysis": context.get("code_analysis"),
                "context_info": context.get("context_info"),
                "root_cause":   context.get("root_cause_analysis"),
                "fix":          context.get("fix_proposal"),
                "tests":        context.get("test_code"),
                "review":       context.get("review_result"),
            },
            "status": "completed",
        }
    