"""Command-line interface for DemoForge using Typer."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from pydantic import HttpUrl
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from demoforge.cache import PipelineCache
from demoforge.config import get_settings
from demoforge.models import AudienceType, PipelineProgress, PipelineStage
from demoforge.pipeline import create_pipeline

# Create Typer app
app = typer.Typer(
    name="demoforge",
    help="🎬 Automated product demo video generator",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


def print_header() -> None:
    """Print DemoForge header."""
    console.print(
        Panel(
            "[bold cyan]DemoForge[/bold cyan] - Automated Demo Video Generator\n"
            "Transform GitHub repos and websites into polished demo videos",
            border_style="cyan",
        )
    )


def validate_url(url_str: str) -> HttpUrl:
    """Validate and parse URL.

    Args:
        url_str: URL string

    Returns:
        Validated HttpUrl

    Raises:
        typer.BadParameter: If URL is invalid
    """
    try:
        return HttpUrl(url_str)
    except Exception:
        raise typer.BadParameter(f"Invalid URL: {url_str}")


@app.command()
def analyze(
    repo: Optional[str] = typer.Option(
        None, "--repo", "-r", help="GitHub repository URL"
    ),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Website URL"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output JSON file path"
    ),
) -> None:
    """Analyze a GitHub repository and/or website.

    Example:
        demoforge analyze --repo https://github.com/expressjs/express
        demoforge analyze --url https://example.com --output analysis.json
    """
    print_header()

    if not repo and not url:
        console.print("[red]Error:[/red] Must provide --repo or --url", style="bold")
        raise typer.Exit(1)

    # Load settings
    settings = get_settings()
    config = settings.to_app_config()

    # Parse URLs
    repo_url = validate_url(repo) if repo else None
    website_url = validate_url(url) if url else None

    # Create pipeline
    pipeline = create_pipeline(config)

    # Progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing...", total=100)

        def update_progress(p: PipelineProgress) -> None:
            progress.update(task, completed=p.progress * 100, description=p.message)

        # Run analysis
        try:
            analysis = asyncio.run(
                pipeline.analyze(
                    repo_url=repo_url,
                    website_url=website_url,
                    progress_callback=update_progress,
                )
            )

            # Display results
            console.print("\n[bold green]✓ Analysis Complete[/bold green]\n")

            table = Table(show_header=False, box=None)
            table.add_column("Field", style="cyan")
            table.add_column("Value")

            table.add_row("Product", analysis.product_name)
            table.add_row("Tagline", analysis.tagline)
            table.add_row("Category", analysis.category)
            table.add_row(
                "Key Features", str(len([f for f in analysis.key_features if f.demo_worthy]))
            )
            table.add_row("Tech Stack", ", ".join(analysis.tech_stack[:5]))

            console.print(table)

            # Save to file if requested
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w") as f:
                    json.dump(analysis.model_dump(mode="json"), f, indent=2)
                console.print(f"\n[green]Saved to:[/green] {output}")

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}", style="bold")
            raise typer.Exit(1)
        finally:
            asyncio.run(pipeline.cleanup())


@app.command()
def script(
    repo: Optional[str] = typer.Option(
        None, "--repo", "-r", help="GitHub repository URL"
    ),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Website URL"),
    audience: AudienceType = typer.Option(
        AudienceType.DEVELOPER, "--audience", "-a", help="Target audience"
    ),
    length: int = typer.Option(90, "--length", "-l", help="Target video length (seconds)"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output JSON file path"
    ),
) -> None:
    """Generate a demo video script.

    Example:
        demoforge script --repo https://github.com/expressjs/express --audience developer
        demoforge script --url https://example.com --audience investor --length 120
    """
    print_header()

    if not repo and not url:
        console.print("[red]Error:[/red] Must provide --repo or --url", style="bold")
        raise typer.Exit(1)

    # Load settings
    settings = get_settings()
    config = settings.to_app_config()

    # Parse URLs
    repo_url = validate_url(repo) if repo else None
    website_url = validate_url(url) if url else None

    # Create pipeline
    pipeline = create_pipeline(config)

    # Progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating script...", total=100)

        def update_progress(p: PipelineProgress) -> None:
            progress.update(task, completed=p.progress * 100, description=p.message)

        # Run pipeline
        try:
            # Analyze
            console.print(f"[cyan]→[/cyan] Analyzing product...")
            analysis = asyncio.run(
                pipeline.analyze(
                    repo_url=repo_url,
                    website_url=website_url,
                    progress_callback=update_progress,
                )
            )

            # Generate script
            console.print(f"[cyan]→[/cyan] Generating {audience.value} script...")
            demo_script = pipeline.generate_script(
                analysis=analysis,
                audience=audience,
                target_duration=length,
                progress_callback=update_progress,
            )

            # Display results
            console.print("\n[bold green]✓ Script Generated[/bold green]\n")

            table = Table(show_header=False, box=None)
            table.add_column("Field", style="cyan")
            table.add_column("Value")

            table.add_row("Title", demo_script.title)
            table.add_row("Audience", demo_script.audience.value)
            table.add_row("Scenes", str(len(demo_script.scenes)))
            table.add_row("Total Words", str(demo_script.total_words))
            table.add_row("Estimated Duration", f"{demo_script.estimated_duration:.1f}s")

            console.print(table)

            # Show scene breakdown
            console.print("\n[bold]Scene Breakdown:[/bold]")
            for i, scene in enumerate(demo_script.scenes, 1):
                console.print(
                    f"  {i}. [{scene.scene_type.value}] {scene.narration[:60]}... ({scene.duration_seconds}s)"
                )

            # Save to file if requested
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w") as f:
                    json.dump(demo_script.model_dump(mode="json"), f, indent=2)
                console.print(f"\n[green]Saved to:[/green] {output}")

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}", style="bold")
            raise typer.Exit(1)
        finally:
            asyncio.run(pipeline.cleanup())


@app.command()
def generate(
    repo: Optional[str] = typer.Option(
        None, "--repo", "-r", help="GitHub repository URL"
    ),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Website URL"),
    audience: AudienceType = typer.Option(
        AudienceType.DEVELOPER, "--audience", "-a", help="Target audience"
    ),
    length: int = typer.Option(90, "--length", "-l", help="Target video length (seconds)"),
    output: Path = typer.Option(
        ..., "--output", "-o", help="Output video file path (e.g., demo.mp4)"
    ),
    project_id: Optional[str] = typer.Option(
        None, "--project-id", help="Project ID (auto-generated if not provided)"
    ),
) -> None:
    """Generate a complete demo video (full pipeline).

    Example:
        demoforge generate --repo https://github.com/expressjs/express \\
                          --audience developer \\
                          --length 120 \\
                          --output express-demo.mp4
    """
    print_header()

    if not repo and not url:
        console.print("[red]Error:[/red] Must provide --repo or --url", style="bold")
        raise typer.Exit(1)

    # Generate project ID if not provided
    if not project_id:
        import hashlib
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        project_id = hashlib.md5(f"{repo or url}{timestamp}".encode()).hexdigest()[:12]

    # Load settings
    settings = get_settings()
    config = settings.to_app_config()

    # Parse URLs
    repo_url = validate_url(repo) if repo else None
    website_url = validate_url(url) if url else None

    # Create pipeline
    pipeline = create_pipeline(config)

    # Progress display
    console.print(f"[cyan]Project ID:[/cyan] {project_id}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        # Create tasks for each stage
        stages = {
            PipelineStage.ANALYZE: progress.add_task("Analyze", total=100),
            PipelineStage.SCRIPT: progress.add_task("Script", total=100),
            PipelineStage.CAPTURE: progress.add_task("Capture", total=100),
            PipelineStage.VOICE: progress.add_task("Voice", total=100),
            PipelineStage.ASSEMBLE: progress.add_task("Assemble", total=100),
        }

        def update_progress(p: PipelineProgress) -> None:
            if p.stage in stages:
                progress.update(
                    stages[p.stage], completed=p.progress * 100, description=p.message
                )

        # Run full pipeline
        try:
            project = asyncio.run(
                pipeline.generate_full_pipeline(
                    project_id=project_id,
                    repo_url=repo_url,
                    website_url=website_url,
                    audience=audience,
                    target_duration=length,
                    output_path=output,
                    progress_callback=update_progress,
                )
            )

            # Display results
            console.print("\n[bold green]✓ Demo Video Generated![/bold green]\n")

            if project.script:
                table = Table(show_header=False, box=None)
                table.add_column("Field", style="cyan")
                table.add_column("Value")

                table.add_row("Project ID", project.id)
                table.add_row("Product", project.analysis.product_name if project.analysis else "N/A")
                table.add_row("Scenes", str(len(project.script.scenes)))
                table.add_row("Output", str(output))

                console.print(table)

                console.print(
                    f"\n[yellow]Note:[/yellow] Phase 2-3 components (capture, voice, assembly) "
                    f"are placeholders. Full video generation coming soon!"
                )

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}", style="bold")
            raise typer.Exit(1)
        finally:
            asyncio.run(pipeline.cleanup())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Server host"),
    port: int = typer.Option(7500, "--port", "-p", help="Server port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """Start the FastAPI web server.

    Example:
        demoforge serve --port 7500 --reload
    """
    import uvicorn

    from demoforge.server.app import create_app

    print_header()
    console.print(f"[cyan]→[/cyan] Starting server on http://{host}:{port}")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

    # Load settings
    settings = get_settings()

    # Create app
    app_instance = create_app(settings)

    # Run server
    uvicorn.run(
        app_instance,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def version() -> None:
    """Show DemoForge version."""
    from demoforge import __version__

    console.print(f"[cyan]DemoForge[/cyan] version [bold]{__version__}[/bold]")


# Cache management commands
cache_app = typer.Typer(
    name="cache",
    help="Manage pipeline cache",
    add_completion=False,
)
app.add_typer(cache_app, name="cache")


@cache_app.command("clear")
def cache_clear() -> None:
    """Clear all pipeline cache entries.

    Example:
        demoforge cache clear
    """
    console.print("[yellow]Clearing pipeline cache...[/yellow]")

    # Load settings
    settings = get_settings()
    cache = PipelineCache(
        cache_dir=settings.cache_dir,
        enabled=True,
        ttl_hours=settings.cache_ttl_hours,
    )

    # Clear cache
    count = cache.clear_all()
    console.print(f"[green]✓ Cleared {count} cache entries[/green]")


@cache_app.command("stats")
def cache_stats() -> None:
    """Show pipeline cache statistics.

    Example:
        demoforge cache stats
    """
    # Load settings
    settings = get_settings()
    cache = PipelineCache(
        cache_dir=settings.cache_dir,
        enabled=True,
        ttl_hours=settings.cache_ttl_hours,
    )

    # Get stats
    stats = cache.get_stats()

    console.print("\n[bold]Pipeline Cache Statistics[/bold]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Status", "Enabled" if stats["enabled"] else "Disabled")
    table.add_row("TTL", f"{stats['ttl_hours']} hours")
    table.add_row("Cached Projects", str(stats["total_projects"]))
    table.add_row("Cached Stages", str(stats["total_stages"]))
    table.add_row("Cache Size", f"{stats['total_size_mb']} MB")

    console.print(table)
    console.print()


@cache_app.command("cleanup")
def cache_cleanup() -> None:
    """Remove expired cache entries.

    Example:
        demoforge cache cleanup
    """
    console.print("[yellow]Removing expired cache entries...[/yellow]")

    # Load settings
    settings = get_settings()
    cache = PipelineCache(
        cache_dir=settings.cache_dir,
        enabled=True,
        ttl_hours=settings.cache_ttl_hours,
    )

    # Cleanup expired
    count = cache.cleanup_expired()
    console.print(f"[green]✓ Removed {count} expired entries[/green]")


if __name__ == "__main__":
    app()
