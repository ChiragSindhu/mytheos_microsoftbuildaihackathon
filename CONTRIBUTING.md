
Now create the **complete demo output formatter**:

### **examples/run_demo.py**
```python
"""Complete demo runner."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import MYTHEOSOrchestrator
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import json

console = Console()

async def main():
    """Run complete demo."""
    
    # Banner
    console.print(Panel.fit(
        "[bold blue] MYTHEOS[/bold blue]\n"
        "[yellow]AI-Powered Multi-Agent Debugging System[/yellow]\n\n"
        "[dim]Microsoft Build AI Hackathon Demo[/dim]",
        border_style="blue"
    ))
    
    # Configuration
    repo_url = "https://github.com/example/sample-buggy-project"
    repo_path = Path(__file__).parent / "sample_buggy_project"
    error_log_path = repo_path / "error_log.txt"
    
    if not error_log_path.exists():
        console.print(f"[red]Error: {error_log_path} not found[/red]")
        return
    
    # Load error
    with open(error_log_path, 'r') as f:
        error_log = f.read()
    
    console.print("\n[bold]📋 Input Error Log:[/bold]")
    console.print(Panel(
        error_log[:400] + "..." if len(error_log) > 400 else error_log,
        title="Stack Trace",
        border_style="red"
    ))
    
    input("\n[yellow]Press Enter to start debugging...[/yellow]")
    
    # Run orchestrator
    orchestrator = MYTHEOSOrchestrator()
    
    try:
        result = await orchestrator.debug(
            repo_url=repo_url,
            error_log=error_log,
            repo_path=str(repo_path),
            language="python"
        )
        
        # Display results
        console.print("\n" + "="*80)
        console.print("[bold green] DEBUGGING COMPLETE![/bold green]")
        console.print("="*80)
        
        # Save results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "full_result.json", 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        console.print(f"\n Full results saved to {output_dir}/full_result.json")
        console.print("\n[green]Demo complete! Check outputs/ directory for all results.[/green]")
        
    except Exception as e:
        console.print(f"\n[red]Error during debugging: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())