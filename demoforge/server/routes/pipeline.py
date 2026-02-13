"""Pipeline execution endpoints."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from demoforge.config import Settings
from demoforge.models import PipelineProgress
from demoforge.pipeline import create_pipeline
from demoforge.server.dependencies import get_app_settings
from demoforge.server.routes.projects import load_project, save_project
from demoforge.server.sse import create_sse_response, sse_manager

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class ExecutePipelineRequest(BaseModel):
    """Request to execute pipeline for a project."""

    project_id: str


async def run_pipeline_task(project_id: str, settings: Settings) -> None:
    """Background task to run the pipeline.

    Args:
        project_id: Project identifier
        settings: Application settings
    """
    try:
        # Load project
        project = load_project(project_id, settings)

        # Create pipeline
        config = settings.to_app_config()
        pipeline = create_pipeline(config)

        # Progress callback
        async def progress_callback(progress: PipelineProgress) -> None:
            await sse_manager.send_progress(project_id, progress)
            # Also save project state
            project.progress = progress
            project.updated_at = progress.updated_at
            save_project(project, settings)

        # Set output path
        if not project.output_path:
            output_dir = settings.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            project.output_path = output_dir / f"{project_id}.mp4"

        # Run pipeline
        updated_project = await pipeline.generate_full_pipeline(
            project_id=project.id,
            repo_url=project.repo_url,
            website_url=project.website_url,
            audience=project.audience,
            target_duration=project.target_length,
            output_path=project.output_path,
            progress_callback=progress_callback,
        )

        # Save final state
        save_project(updated_project, settings)

        # Cleanup
        await pipeline.cleanup()

    except Exception as e:
        # Send error via SSE
        error_progress = PipelineProgress(
            stage=project.current_stage,
            progress=0.0,
            message=f"Pipeline failed: {str(e)}",
            error=str(e),
        )
        await sse_manager.send_progress(project_id, error_progress)

    finally:
        # Close SSE connection
        await sse_manager.close_connection(project_id)


@router.post("/execute")
async def execute_pipeline(
    request: ExecutePipelineRequest,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, str]:
    """Execute the pipeline for a project.

    Args:
        request: Pipeline execution request
        background_tasks: FastAPI background tasks
        settings: Application settings

    Returns:
        Execution confirmation
    """
    # Verify project exists
    load_project(request.project_id, settings)

    # Start pipeline in background
    background_tasks.add_task(run_pipeline_task, request.project_id, settings)

    return {
        "status": "started",
        "project_id": request.project_id,
        "stream_url": f"/api/pipeline/progress/{request.project_id}",
    }


@router.get("/progress/{project_id}")
async def get_pipeline_progress(
    project_id: str,
    settings: Annotated[Settings, Depends(get_app_settings)]
):
    """Stream pipeline progress via Server-Sent Events.

    Args:
        project_id: Project identifier
        settings: Application settings

    Returns:
        SSE stream of progress updates
    """
    # Verify project exists
    load_project(project_id, settings)

    return create_sse_response(project_id)
