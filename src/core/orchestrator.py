"""Main orchestrator for the debugging swarm - follows exact flow diagram."""
from typing import Dict, Any, Optional
import asyncio
from rich.console import Console
from rich.tree import Tree
from src.core.state import SwarmState
from src.agents.planner import PlannerAgent
from src.agents.reproduction import ReproductionAgent
from src.agents.code_analysis import CodeAnalysisAgent
from src.agents.context import ContextAgent
from src.agents.root_cause import RootCauseAgent
from src.agents.fix import FixAgent
from src.agents.test import TestAgent
from src.agents.review import ReviewAgent
from src.utils.logger import get_logger
from src.utils.formatters import format_bug_report, format_pull_request

logger = get_logger(__name__)
console = Console()

class MYTHEOSOrchestrator:
    """Orchestrates the debugging swarm following the exact flow."""
    
    def __init__(self):
        self.state = SwarmState()
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
        self.context = {}
    
    def print_flow_diagram(self):
        """Print the agent flow diagram."""
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
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Run the complete debugging process.
        
        Flow:
        1. Input: GitHub Repo + Error Logs
        2. Planner Agent
        3. Parallel: Repro + Code Analysis + Context
        4. Root Cause Agent
        5. Fix Agent
        6. Test Agent
        7. Review Agent
        8. Output: PR + Report
        """
        logger.info(f" Starting debug process for {repo_url}")
        self.print_flow_diagram()
        
        # ============================================
        # PHASE 0: Input Preparation
        # ============================================
        console.print("\n[bold yellow] PHASE 0: Input Preparation[/bold yellow]")
        
        self.context = {
            "repo_url": repo_url,
            "repo_path": repo_path,
            "error_log": error_log,
            "issue_id": issue_id,
            "language": language,
            "repo_name": repo_url.split("/")[-1],
        }
        
        # Load repository files
        if repo_path:
            self.context["relevant_code"] = self._load_relevant_code(repo_path, error_log)
            self.context["repo_structure"] = self._get_repo_structure(repo_path)
        
        console.print(f" Loaded repository: {self.context['repo_name']}")
        console.print(f" Language: {language}")
        
        # ============================================
        # PHASE 1: Planning
        # ============================================
        console.print("\n[bold cyan] PHASE 1: Planning[/bold cyan]")
        logger.info("Planner Agent: Creating debugging strategy...")
        
        plan_result = self.agents["planner"].process(self.context)
        self.context.update(plan_result)
        
        console.print(" Debugging plan created")
        
        # ============================================
        # PHASE 2: Parallel Information Gathering
        # ============================================
        console.print("\n[bold magenta] PHASE 2: Parallel Information Gathering[/bold magenta]")
        
        # Run three agents in parallel
        logger.info("Running Reproduction, Code Analysis, and Context agents in parallel...")
        
        async def run_parallel_agents():
            tasks = [
                asyncio.to_thread(self.agents["reproduction"].process, self.context),
                asyncio.to_thread(self.agents["code_analysis"].process, self.context),
                asyncio.to_thread(self.agents["context"].process, self.context),
            ]
            return await asyncio.gather(*tasks)
        
        repro_result, code_result, context_result = await run_parallel_agents()
        
        console.print("   Reproduction Agent: Complete")
        console.print("   Code Analysis Agent: Complete")
        console.print("   Context Agent: Complete")
        
        # Merge results
        self.context.update(repro_result)
        self.context.update(code_result)
        self.context.update(context_result)
        
        # ============================================
        # PHASE 3: Root Cause Analysis
        # ============================================
        console.print("\n[bold red] PHASE 3: Root Cause Analysis[/bold red]")
        logger.info("Root Cause Agent: Identifying root cause...")
        
        root_cause_result = self.agents["root_cause"].process(self.context)
        self.context.update(root_cause_result)
        
        console.print(" Root cause identified")
        
        # ============================================
        # PHASE 4: Fix Generation
        # ============================================
        console.print("\n[bold green]🔧 PHASE 4: Fix Generation[/bold green]")
        logger.info("Fix Agent: Generating code fix...")
        
        fix_result = self.agents["fix"].process(self.context)
        self.context.update(fix_result)
        
        console.print(" Fix generated")
        
        # ============================================
        # PHASE 5: Test Generation
        # ============================================
        console.print("\n[bold blue] PHASE 5: Test Generation[/bold blue]")
        logger.info("Test Agent: Creating test cases...")
        
        test_result = self.agents["test"].process(self.context)
        self.context.update(test_result)
        
        console.print(" Tests generated")
        
        # ============================================
        # PHASE 6: Code Review
        # ============================================
        console.print("\n[bold yellow] PHASE 6: Code Review[/bold yellow]")
        logger.info("Review Agent: Reviewing fix and tests...")
        
        review_result = self.agents["review"].process(self.context)
        self.context.update(review_result)
        
        console.print(" Review complete")
        
        # ============================================
        # PHASE 7: Generate Output
        # ============================================
        console.print("\n[bold green] PHASE 7: Generating Output[/bold green]")
        
        output = self._generate_output(self.context)
        
        console.print(" Bug report generated")
        console.print(" Pull request prepared")
        
        return output
    
    def _load_relevant_code(self, repo_path: str, error_log: str) -> str:
        """Load relevant code files based on error log."""
        # In production, parse error log for file paths
        # For now, return sample
        import os
        code_snippets = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            relative_path = os.path.relpath(file_path, repo_path)
                            code_snippets.append(f"\n--- {relative_path} ---\n{content}")
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        
        return "\n".join(code_snippets[:5])  # Limit to first 5 files
    
    def _get_repo_structure(self, repo_path: str) -> str:
        """Get repository structure."""
        import os
        structure = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv']]
            
            level = root.replace(repo_path, '').count(os.sep)
            indent = ' ' * 2 * level
            structure.append(f'{indent}{os.path.basename(root)}/')
            
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                structure.append(f'{sub_indent}{file}')
        
        return '\n'.join(structure[:50])  # Limit output
    
    def _generate_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final bug report and PR."""
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
            "status": "completed"
        }
    