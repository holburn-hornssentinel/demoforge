"""Project management endpoints."""

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from demoforge.config import Settings
from demoforge.models import AudienceType, ProjectState

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    """Request to create a new project."""

    name: str
    repo_url: HttpUrl | None = None
    website_url: HttpUrl | None = None
    audience: AudienceType = AudienceType.DEVELOPER
    target_length: int = 90


class ProjectResponse(BaseModel):
    """Project response."""

    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    repo_url: HttpUrl | None
    website_url: HttpUrl | None
    audience: AudienceType
    target_length: int
    current_stage: str
    output_path: str | None


def get_projects_dir(settings: Settings) -> Path:
    """Get projects directory path.

    Args:
        settings: Application settings

    Returns:
        Projects directory path
    """
    projects_dir = settings.cache_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def load_project(project_id: str, settings: Settings) -> ProjectState:
    """Load project from disk.

    Args:
        project_id: Project identifier
        settings: Application settings

    Returns:
        Project state

    Raises:
        HTTPException: If project not found
    """
    projects_dir = get_projects_dir(settings)
    project_file = projects_dir / f"{project_id}.json"

    if not project_file.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    with open(project_file) as f:
        data = json.load(f)
        return ProjectState.model_validate(data)


def save_project(project: ProjectState, settings: Settings) -> None:
    """Save project to disk.

    Args:
        project: Project state
        settings: Application settings
    """
    projects_dir = get_projects_dir(settings)
    project_file = projects_dir / f"{project.id}.json"

    with open(project_file, "w") as f:
        json.dump(project.model_dump(mode="json"), f, indent=2)


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    settings: Annotated[Settings, Depends()],
) -> ProjectResponse:
    """Create a new demo project.

    Args:
        request: Project creation request
        settings: Application settings

    Returns:
        Created project
    """
    import hashlib

    # Generate project ID
    timestamp = datetime.now().isoformat()
    project_id = hashlib.md5(
        f"{request.name}{timestamp}".encode()
    ).hexdigest()[:12]

    # Create project state
    project = ProjectState(
        id=project_id,
        name=request.name,
        repo_url=request.repo_url,
        website_url=request.website_url,
        audience=request.audience,
        target_length=request.target_length,
    )

    # Save to disk
    save_project(project, settings)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        repo_url=project.repo_url,
        website_url=project.website_url,
        audience=project.audience,
        target_length=project.target_length,
        current_stage=project.current_stage.value,
        output_path=str(project.output_path) if project.output_path else None,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    settings: Annotated[Settings, Depends()],
) -> list[ProjectResponse]:
    """List all projects.

    Args:
        settings: Application settings

    Returns:
        List of projects
    """
    projects_dir = get_projects_dir(settings)
    projects = []

    for project_file in projects_dir.glob("*.json"):
        with open(project_file) as f:
            data = json.load(f)
            project = ProjectState.model_validate(data)
            projects.append(
                ProjectResponse(
                    id=project.id,
                    name=project.name,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    repo_url=project.repo_url,
                    website_url=project.website_url,
                    audience=project.audience,
                    target_length=project.target_length,
                    current_stage=project.current_stage.value,
                    output_path=str(project.output_path) if project.output_path else None,
                )
            )

    # Sort by updated_at descending
    projects.sort(key=lambda p: p.updated_at, reverse=True)
    return projects


@router.get("/{project_id}", response_model=ProjectState)
async def get_project(
    project_id: str,
    settings: Annotated[Settings, Depends()],
) -> ProjectState:
    """Get project details.

    Args:
        project_id: Project identifier
        settings: Application settings

    Returns:
        Project state
    """
    return load_project(project_id, settings)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    settings: Annotated[Settings, Depends()],
) -> dict[str, str]:
    """Delete a project.

    Args:
        project_id: Project identifier
        settings: Application settings

    Returns:
        Deletion confirmation
    """
    projects_dir = get_projects_dir(settings)
    project_file = projects_dir / f"{project_id}.json"

    if not project_file.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    project_file.unlink()
    return {"status": "deleted", "project_id": project_id}
