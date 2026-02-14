"""Analytics API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from demoforge.analytics import AnalyticsTracker, ProjectAnalytics, ViewEvent
from demoforge.config import Settings
from demoforge.server.dependencies import get_app_settings

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class TrackViewRequest(BaseModel):
    """Request to track a view event."""

    project_id: str
    event_type: str  # play, pause, complete, heartbeat
    progress: float = 0.0  # 0-1
    duration: float | None = None


@router.post("/view")
async def track_view(
    request: Request,
    data: TrackViewRequest,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, str]:
    """Track a video view event.

    Args:
        request: HTTP request (for IP and user agent)
        data: View event data
        settings: Application settings

    Returns:
        Success confirmation
    """
    tracker = AnalyticsTracker(analytics_dir=settings.cache_dir / "analytics")

    # Create event
    event = ViewEvent(
        project_id=data.project_id,
        event_type=data.event_type,
        progress=data.progress,
        duration=data.duration,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    # Track event
    tracker.track_event(event)

    return {"status": "tracked", "event_type": data.event_type}


@router.get("/{project_id}")
async def get_project_analytics(
    project_id: str,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProjectAnalytics:
    """Get analytics for a specific project.

    Args:
        project_id: Project identifier
        settings: Application settings

    Returns:
        Project analytics summary
    """
    tracker = AnalyticsTracker(analytics_dir=settings.cache_dir / "analytics")
    return tracker.get_analytics(project_id)


@router.get("/")
async def get_all_analytics(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, ProjectAnalytics]:
    """Get analytics for all projects.

    Args:
        settings: Application settings

    Returns:
        Dictionary mapping project_id to analytics
    """
    tracker = AnalyticsTracker(analytics_dir=settings.cache_dir / "analytics")
    return tracker.get_all_analytics()
