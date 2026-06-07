"""Main orchestrator for the debugging swarm.

Accepts a ProgressEmitter for progress reporting.
Has zero knowledge of SSE, WebSockets, or any transport.
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
from src.core.state import SwarmState
from src.utils.formatters import format_bug_report, format_pull_request
from src.utils.logger import get_logger
from src.core.progress_emitter import ProgressEmitter

logger = get_logger(__name__)
console = Console()


class MYTHEOSOrchestrator:
    """
    Orchestrates the debugging swarm following the exact flow.

    Args:
        emitter: Optional ProgressEmitter. When provided, real-time phase
                 events are emitted as each agent runs. When omitted the
                 orchestrator works in silent/CLI mode.
    """

    def __init__(self, emitter: Optional[ProgressEmitter] = None):
        self.state = SwarmState()
        self.emitter = emitter
        self.agents = {
            "planner": PlannerAgent(),
            "reproduction": ReproductionAgent(),
            "code_analysis": CodeAnalysisAgent(),
            "context": ContextAgent(),
            "root_cause": RootCauseAgent(),
            "fix": FixAgent(),
            "test": TestAgent(),
            "review": ReviewAgent(),
        }
        self.context: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Internal helper — emit only when an emitter is attached
    # ------------------------------------------------------------------

    async def _emit(self, phase: str, message: str, *, done: bool = False, **extra: Any) -> None:
        if self.emitter:
            await self.emitter.emit(phase, message, done=done, **extra)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def print_flow_diagram(self) -> None:
        tree = Tree(" [bold blue]MYTHEOS Flow[/bold blue]")
        input_node = tree.add(" [yellow]GitHub Repo + Error Logs[/yellow]")
        planner_node = input_node.add(" [cyan]Planner Agent[/cyan]")
        parallel_node = planner_node.add(" [magenta]Parallel Analysis[/magenta]")
        parallel_node.add(" Reproduction Agent")
        parallel_node.add(" Code Analysis Agent")
        parallel_node.add(" Context Agent")
        root_cause_node = planner_node.add(" [red]Root Cause Agent[/red]")
        fix_node = root_cause_node.add("🔧 [green]Fix Agent[/green]")
        test_node = fix_node.add(" [blue]Test Agent[/blue]")
        review_node = test_node.add(" [yellow]Review Agent[/yellow]")
        review_node.add(" [bold green]Pull Request + Report[/bold green]")
        console.print(tree)

    async def debug(
        self,
        repo_url: str,
        error_log: str,
        repo_path: Optional[str] = None,
        issue_id: Optional[str] = None,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        Run the complete debugging process, emitting progress events at each phase.

        Flow:
          0. Input preparation
          1. Planner
          2. Parallel: Reproduction + Code Analysis + Context
          3. Root Cause
          4. Fix
          5. Test
          6. Review
          7. Output generation
        """
        logger.info("Starting debug process for %s", repo_url)
        self.print_flow_diagram()

        # ── PHASE 0: input prep ──────────────────────────────────────────
        await self._emit("initialization", "Preparing repository context...")

        self.context = {
            "repo_url": repo_url,
            "repo_path": repo_path,
            "error_log": error_log,
            "issue_id": issue_id,
            "language": language,
            "repo_name": repo_url.split("/")[-1],
        }

        if repo_path:
            self.context["relevant_code"] = self._load_relevant_code(repo_path, error_log)
            self.context["repo_structure"] = self._get_repo_structure(repo_path)

        await self._emit("initialization", "Repository context ready.", done=True)

        # ── PHASE 1: planner ─────────────────────────────────────────────
        console.print("\n[bold cyan] PHASE 1: Planning[/bold cyan]")
        await self._emit("planning", "Planner agent creating debugging strategy...")

        plan_result = await asyncio.to_thread(self.agents["planner"].process, self.context)
        self.context.update(plan_result)

        await self._emit("planning", "Debugging plan created.", done=True,
                         plan=plan_result.get("plan", ""))

        # ── PHASE 2: parallel agents ──────────────────────────────────────
        console.print("\n[bold magenta] PHASE 2: Parallel Information Gathering[/bold magenta]")
        await self._emit(
            "parallel_start",
            "Starting parallel analysis: Reproduction · Code Analysis · Context"
        )

        repro_result, code_result, ctx_result = await asyncio.gather(
            asyncio.to_thread(self.agents["reproduction"].process, self.context),
            asyncio.to_thread(self.agents["code_analysis"].process, self.context),
            asyncio.to_thread(self.agents["context"].process, self.context),
        )

        self.context.update(repro_result)
        self.context.update(code_result)
        self.context.update(ctx_result)

        console.print("   Reproduction Agent: Complete")
        console.print("   Code Analysis Agent: Complete")
        console.print("   Context Agent: Complete")

        await self._emit(
            "parallel_done",
            "Reproduction · Code Analysis · Context complete.",
            done=True,
            reproduction=repro_result.get("reproduction_info", ""),
            code_analysis=code_result.get("code_analysis", ""),
            context_info=ctx_result.get("context_info", ""),
        )

        # ── PHASE 3: root cause ───────────────────────────────────────────
        console.print("\n[bold red] PHASE 3: Root Cause Analysis[/bold red]")
        await self._emit("root_cause", "Root cause agent identifying source of bug...")

        root_cause_result = await asyncio.to_thread(
            self.agents["root_cause"].process, self.context
        )
        self.context.update(root_cause_result)

        await self._emit("root_cause", "Root cause identified.", done=True,
                         root_cause=root_cause_result.get("root_cause_analysis", ""))

        # ── PHASE 4: fix ──────────────────────────────────────────────────
        console.print("\n[bold green]🔧 PHASE 4: Fix Generation[/bold green]")
        await self._emit("fix", "Fix agent generating code solution...")

        fix_result = await asyncio.to_thread(self.agents["fix"].process, self.context)
        self.context.update(fix_result)

        await self._emit("fix", "Fix generated.", done=True,
                         fix=fix_result.get("fix_proposal", ""))

        # ── PHASE 5: tests ────────────────────────────────────────────────
        console.print("\n[bold blue] PHASE 5: Test Generation[/bold blue]")
        await self._emit("test", "Test agent creating test cases...")

        test_result = await asyncio.to_thread(self.agents["test"].process, self.context)
        self.context.update(test_result)

        await self._emit("test", "Tests generated.", done=True,
                         tests=test_result.get("test_code", ""))

        # ── PHASE 6: review ───────────────────────────────────────────────
        console.print("\n[bold yellow] PHASE 6: Code Review[/bold yellow]")
        await self._emit("review", "Review agent validating solution...")

        review_result = await asyncio.to_thread(self.agents["review"].process, self.context)
        self.context.update(review_result)

        await self._emit("review", "Review complete.", done=True,
                         review=review_result.get("review_result", ""))

        # ── PHASE 7: output ───────────────────────────────────────────────
        console.print("\n[bold green] PHASE 7: Generating Output[/bold green]")
        await self._emit("output", "Generating bug report and pull request...")

        output = self._generate_output(self.context)

        await self._emit("output", "Output ready.", done=True)

        return output

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_relevant_code(self, repo_path: str, error_log: str) -> str:
        code_snippets = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", "venv"}]
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            relative = os.path.relpath(file_path, repo_path)
                            code_snippets.append(f"\n--- {relative} ---\n{f.read()}")
                    except Exception as e:
                        logger.warning("Could not read %s: %s", file_path, e)
        return "\n".join(code_snippets[:5])

    def _get_repo_structure(self, repo_path: str) -> str:
        structure = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", "venv"}]
            level = root.replace(repo_path, "").count(os.sep)
            structure.append(f"{'  ' * level}{os.path.basename(root)}/")
            for file in files:
                structure.append(f"{'  ' * (level + 1)}{file}")
        return "\n".join(structure[:50])

    def _generate_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "bug_report": format_bug_report(context),
            "pull_request": format_pull_request(context),
            "context": {
                "plan": context.get("plan"),
                "reproduction": context.get("reproduction_info"),
                "code_analysis": context.get("code_analysis"),
                "context_info": context.get("context_info"),
                "root_cause": context.get("root_cause_analysis"),
                "fix": context.get("fix_proposal"),
                "tests": context.get("test_code"),
                "review": context.get("review_result"),
            },
            "status": "completed",
        }