"""CLI interface for MYTHEOS."""
import click
import asyncio
import sys
import traceback
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from src.core.orchestrator import MYTHEOSOrchestrator
from src.core.local_file_debugger import LocalFileDebugger
from config.settings import settings
import json

console = Console()

@click.group()
def cli():
    """ MYTHEOS - AI-powered debugging assistant."""
    pass

@cli.command()
@click.option("--repo", help="GitHub repository URL")
@click.option("--error-log", type=click.File("r"), help="Error log file")
@click.option("--error-text", help="Error text directly")
@click.option("--issue", help="GitHub issue ID")
@click.option("--output", default="outputs/", help="Output directory")
def debug(repo, error_log, error_text, issue, output):
    """Start debugging process for GitHub repo."""
    console.print("[bold blue] MYTHEOS Starting...[/bold blue]")
    
    error_content = error_text or (error_log.read() if error_log else None)
    
    if not error_content:
        console.print("[red]Error: Provide either --error-log or --error-text[/red]")
        return
    
    orchestrator = MYTHEOSOrchestrator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Debugging...", total=None)
        
        result = asyncio.run(orchestrator.debug(
            repo_url=repo,
            error_log=error_content,
            issue_id=issue
        ))
    
    console.print("\n[bold green] Debugging Complete![/bold green]")
    console.print(f"\n[bold]Root Cause:[/bold]\n{result['bug_report']['root_cause']}")
    console.print(f"\n[bold]Pull Request:[/bold]\n{result['pull_request']['title']}")

    # Save reports
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    repo_name = (repo.rstrip("/").split("/")[-1] if repo else "debug_session")

    json_file = output_dir / f"{repo_name}_debug_report.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    md_file = output_dir / f"{repo_name}_debug_report.md"
    save_markdown_report(result, md_file, "MYTHEOS Repository Debug Report")

    console.print(f"\nJSON Report saved to: [cyan]{json_file}[/cyan]")
    console.print(f"Markdown Report saved to: [cyan]{md_file}[/cyan]")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--auto-run/--no-auto-run', default=True, help='Automatically run file to detect errors')
@click.option('--test-file', type=click.Path(exists=True), help='Test file to run')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def test_file(file_path, auto_run, test_file, verbose):
    """
    Test a local Python file for bugs.
    
    Examples:
        mytheos test-file buggy_code.py
        mytheos test-file app.py --test-file tests/test_app.py
        mytheos test-file script.py --no-auto-run
    """
    console.print(Panel.fit(
        f"[bold blue] Mytheos Testing Local File[/bold blue]\n"
        f"[yellow]{file_path}[/yellow]",
        border_style="blue"
    ))
    
    debugger = LocalFileDebugger(verbose=verbose)
    
    result = asyncio.run(debugger.debug_file(
        file_path=file_path,
        auto_run=auto_run,
        test_file=test_file
    ))
    
    # Display results
    _display_local_results(result)
    
    # Save results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    file_name = Path(file_path).stem
    output_file = output_dir / f"{file_name}_debug_report.json"
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    console.print(f"\n Report saved to: [cyan]{output_file}[/cyan]")

    md_file = output_dir / f"{file_name}_debug_report.md"
    save_markdown_report(result, md_file, "Mytheos Debug Report")
    console.print(f"Markdown Report saved to: [cyan]{md_file}[/cyan]")

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.py', help='File pattern to match')
def scan_directory(directory, pattern):
    """Scan entire directory for potential bugs."""
    console.print(f"[bold blue] Scanning directory:[/bold blue] {directory}")
    
    debugger = LocalFileDebugger()
    files = list(Path(directory).rglob(pattern))
    
    console.print(f"Found {len(files)} Python files")
    
    results = {}
    for file_path in files:
        console.print(f"\n[yellow]Testing:[/yellow] {file_path}")
        try:
            result = asyncio.run(debugger.debug_file(str(file_path), auto_run=True))
            if result.get('errors_found'):
                results[str(file_path)] = result
        except Exception as e:
            console.print(f"[red]Error testing {file_path}: {e}[/red]")
    
    console.print(f"\n[bold green] Scan complete![/bold green]")
    console.print(f"Files with issues: {len(results)}")
    
    if results:
        output_file = Path("outputs") / "directory_scan_report.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        console.print(f"Report saved to: {output_file}")

def save_markdown_report(data: dict, output_path: Path, title: str):
    def flatten_dict(data, parent_key=""):
        """Flatten nested dict/list structure."""
        items = {}

        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                items.update(flatten_dict(v, new_key))

        elif isinstance(data, list):
            for i, v in enumerate(data):
                new_key = f"{parent_key}[{i}]"
                items.update(flatten_dict(v, new_key))

        else:
            items[parent_key] = data

        return items

    flat = flatten_dict(data)
    lines = [f"# {title}", ""]
    for key, value in flat.items():
        lines.append(f"## {key}")
        lines.append("")
        if isinstance(value, str):
            lines.extend(["```", value, "```"])
        else:
            lines.append(f"`{value}`")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

@cli.command()
def examples():
    """Run example buggy files."""
    console.print("[bold blue] Running Example Bugs[/bold blue]\n")
    
    examples_dir = Path("examples/buggy_files")
    if not examples_dir.exists():
        console.print("[red]Examples directory not found![/red]")
        return
    
    levels = ['easy', 'medium', 'hard']
    
    for level in levels:
        file_path = examples_dir / f"{level}_bug.py"
        if file_path.exists():
            console.print(f"\n{'='*60}")
            console.print(f"[bold yellow]Testing {level.upper()} bug[/bold yellow]")
            console.print(f"{'='*60}\n")
            
            debugger = LocalFileDebugger(verbose=False)
            result = asyncio.run(debugger.debug_file(str(file_path), auto_run=True))
            
            _display_local_results(result, brief=True)
            
            input(f"\n[dim]Press Enter to continue to next example...[/dim]")

@cli.command()
def providers():
    """List available LLM providers."""
    console.print(f"[bold]Current Provider:[/bold] {settings.LLM_PROVIDER}")
    console.print(f"[bold]Current Model:[/bold] {settings.GROQ_MODEL}")

def _display_local_results(result: dict, brief: bool = False):
    """Display results from local file debugging."""
    
    if result.get('execution_error'):
        console.print("\n[bold red] Execution Error Detected![/bold red]")
        console.print(Panel(
            result['execution_error'][:500],
            title="Error Output",
            border_style="red"
        ))
    else:
        console.print("\n[bold green] File executed without errors[/bold green]")
        if result.get('output'):
            console.print(Panel(
                result['output'][:300],
                title="Output",
                border_style="green"
            ))
    
    if not brief and result.get('analysis'):
        console.print("\n[bold cyan] Analysis:[/bold cyan]")
        analysis = result['analysis']
        
        if analysis.get('root_cause'):
            console.print(Panel(
                analysis['root_cause'][:400],
                title="Root Cause",
                border_style="yellow"
            ))
        
        if analysis.get('fix'):
            console.print("\n[bold green]🔧 Suggested Fix:[/bold green]")
            console.print(Panel(
                analysis['fix'][:400],
                title="Fix",
                border_style="green"
            ))
        
        if analysis.get('tests'):
            console.print("\n[bold blue] Suggested Tests:[/bold blue]")
            console.print(Panel(
                analysis['tests'][:400],
                title="Tests",
                border_style="blue"
            ))

if __name__ == "__main__":
    cli()