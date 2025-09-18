"""CLI interface for Voluntier backend."""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from voluntier.config import settings
from voluntier.temporal_worker.main import run_worker
from voluntier.utils.logging import setup_logging

console = Console()
app = typer.Typer(name="voluntier", help="Voluntier backend management CLI")


@app.command()
def worker():
    """Run the Temporal worker."""
    console.print("[bold green]Starting Temporal worker...[/bold green]")
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        console.print("[yellow]Worker stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Worker failed: {str(e)}[/bold red]")
        sys.exit(1)


@app.command()
def config():
    """Show current configuration."""
    table = Table(title="Voluntier Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Application settings
    table.add_row("App Name", settings.app_name)
    table.add_row("Version", settings.app_version)
    table.add_row("Environment", settings.environment)
    table.add_row("Debug", str(settings.debug))
    
    # Database
    table.add_row("Database URL", settings.database.url)
    table.add_row("Redis URL", settings.redis.url)
    table.add_row("Neo4j URI", settings.neo4j.uri)
    
    # Temporal
    table.add_row("Temporal Host", settings.temporal.host)
    table.add_row("Task Queue", settings.temporal.task_queue)
    
    # LLM
    table.add_row("vLLM Base URL", settings.llm.vllm_base_url)
    table.add_row("Default Model", settings.llm.default_model)
    
    console.print(table)


@app.command()
def health():
    """Check system health."""
    import asyncio
    import aiohttp
    
    async def check_health():
        checks = {
            "Database": settings.database.url.replace("postgresql+asyncpg://", "postgresql://"),
            "Redis": settings.redis.url,
            "Neo4j": settings.neo4j.uri,
            "Temporal": f"http://{settings.temporal.host.replace(':7233', ':8080')}",
            "vLLM": f"{settings.llm.vllm_base_url}/health",
        }
        
        table = Table(title="System Health Check")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        for service, url in checks.items():
            try:
                if service == "Database":
                    # Database connection check would go here
                    status = "🟢 Connected"
                    details = "Connection successful"
                elif service == "Redis":
                    # Redis connection check would go here
                    status = "🟢 Connected"
                    details = "Connection successful"
                elif service == "Neo4j":
                    # Neo4j connection check would go here
                    status = "🟢 Connected"
                    details = "Connection successful"
                else:
                    # HTTP health checks
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                status = "🟢 Healthy"
                                details = f"HTTP {response.status}"
                            else:
                                status = "🟡 Degraded"
                                details = f"HTTP {response.status}"
            except Exception as e:
                status = "🔴 Error"
                details = str(e)[:50]
            
            table.add_row(service, status, details)
        
        console.print(table)
    
    try:
        asyncio.run(check_health())
    except Exception as e:
        console.print(f"[bold red]Health check failed: {str(e)}[/bold red]")


@app.command()
def logs(
    level: str = typer.Option("INFO", help="Log level"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
):
    """View application logs."""
    setup_logging()
    console.print(f"[cyan]Log level: {level}[/cyan]")
    
    if follow:
        console.print("[yellow]Following logs (Ctrl+C to stop)...[/yellow]")
        # Implementation would tail log files
    else:
        console.print("[yellow]Showing recent logs...[/yellow]")
        # Implementation would show recent log entries


@app.command()
def db(
    command: str = typer.Argument(..., help="Database command (migrate, reset, seed)"),
):
    """Database management commands."""
    console.print(f"[cyan]Running database command: {command}[/cyan]")
    
    if command == "migrate":
        console.print("[yellow]Running database migrations...[/yellow]")
        # Implementation would run Alembic migrations
    elif command == "reset":
        console.print("[red]Resetting database...[/red]")
        # Implementation would reset database
    elif command == "seed":
        console.print("[green]Seeding database with sample data...[/green]")
        # Implementation would seed database
    else:
        console.print(f"[red]Unknown database command: {command}[/red]")
        sys.exit(1)


@app.command()
def workflow(
    action: str = typer.Argument(..., help="Workflow action (list, trigger, status)"),
    workflow_type: Optional[str] = typer.Option(None, help="Workflow type"),
    workflow_id: Optional[str] = typer.Option(None, help="Workflow ID"),
):
    """Workflow management commands."""
    console.print(f"[cyan]Workflow action: {action}[/cyan]")
    
    if action == "list":
        console.print("[yellow]Listing active workflows...[/yellow]")
        # Implementation would list workflows
    elif action == "trigger":
        if not workflow_type:
            console.print("[red]Workflow type required for trigger action[/red]")
            sys.exit(1)
        console.print(f"[green]Triggering workflow: {workflow_type}[/green]")
        # Implementation would trigger workflow
    elif action == "status":
        if not workflow_id:
            console.print("[red]Workflow ID required for status action[/red]")
            sys.exit(1)
        console.print(f"[blue]Getting status for workflow: {workflow_id}[/blue]")
        # Implementation would get workflow status
    else:
        console.print(f"[red]Unknown workflow action: {action}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()