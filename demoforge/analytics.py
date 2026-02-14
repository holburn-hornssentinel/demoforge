"""Video analytics and view tracking for DemoForge.

Tracks video views, completion rates, and engagement metrics using JSONL storage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ViewEvent(BaseModel):
    """A video view event."""

    project_id: str = Field(..., description="Project identifier")
    event_type: str = Field(
        ..., description="Event type (play, pause, complete, heartbeat)"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Playback progress (0-1)")
    duration: float | None = Field(None, description="Video duration in seconds")
    user_agent: str | None = Field(None, description="User agent string")
    ip_address: str | None = Field(None, description="Client IP address (anonymized)")


class ProjectAnalytics(BaseModel):
    """Analytics summary for a project."""

    project_id: str
    total_views: int = 0
    unique_views: int = 0  # Approximation based on IP+UA
    total_plays: int = 0
    total_completes: int = 0
    completion_rate: float = 0.0  # Percentage
    average_watch_time: float = 0.0  # Seconds
    last_viewed: datetime | None = None


class AnalyticsTracker:
    """Tracks and stores video analytics."""

    def __init__(self, analytics_dir: Path = Path("/app/cache/analytics")) -> None:
        """Initialize analytics tracker.

        Args:
            analytics_dir: Directory to store analytics JSONL files
        """
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

    def _get_events_file(self, project_id: str) -> Path:
        """Get path to events JSONL file for a project.

        Args:
            project_id: Project identifier

        Returns:
            Path to events file
        """
        return self.analytics_dir / f"{project_id}_events.jsonl"

    def track_event(self, event: ViewEvent) -> None:
        """Record a view event.

        Args:
            event: View event to track
        """
        events_file = self._get_events_file(event.project_id)

        # Append to JSONL file
        with open(events_file, "a") as f:
            f.write(event.model_dump_json() + "\n")

    def get_events(self, project_id: str, limit: int | None = None) -> list[ViewEvent]:
        """Retrieve view events for a project.

        Args:
            project_id: Project identifier
            limit: Maximum number of events to return (None for all)

        Returns:
            List of view events
        """
        events_file = self._get_events_file(project_id)

        if not events_file.exists():
            return []

        events = []
        with open(events_file, "r") as f:
            for line in f:
                try:
                    event_data = json.loads(line.strip())
                    events.append(ViewEvent(**event_data))
                except (json.JSONDecodeError, ValueError):
                    # Skip invalid lines
                    continue

        # Return most recent first
        events.reverse()

        if limit:
            return events[:limit]
        return events

    def get_analytics(self, project_id: str) -> ProjectAnalytics:
        """Calculate analytics for a project.

        Args:
            project_id: Project identifier

        Returns:
            Analytics summary
        """
        events = self.get_events(project_id)

        if not events:
            return ProjectAnalytics(project_id=project_id)

        # Count events by type
        plays = sum(1 for e in events if e.event_type == "play")
        completes = sum(1 for e in events if e.event_type == "complete")

        # Estimate unique views (by IP + User Agent)
        unique_identifiers = set()
        for event in events:
            if event.event_type == "play":
                identifier = f"{event.ip_address}:{event.user_agent}"
                unique_identifiers.add(identifier)

        unique_views = len(unique_identifiers)

        # Calculate completion rate
        completion_rate = (completes / plays * 100) if plays > 0 else 0.0

        # Calculate average watch time from progress events
        watch_times = []
        for event in events:
            if event.duration and event.progress > 0:
                watch_time = event.duration * event.progress
                watch_times.append(watch_time)

        avg_watch_time = sum(watch_times) / len(watch_times) if watch_times else 0.0

        # Get last viewed timestamp
        last_viewed = max((e.timestamp for e in events), default=None)

        return ProjectAnalytics(
            project_id=project_id,
            total_views=len(events),
            unique_views=unique_views,
            total_plays=plays,
            total_completes=completes,
            completion_rate=round(completion_rate, 2),
            average_watch_time=round(avg_watch_time, 2),
            last_viewed=last_viewed,
        )

    def get_all_analytics(self) -> dict[str, ProjectAnalytics]:
        """Get analytics for all projects.

        Returns:
            Dictionary mapping project_id to analytics
        """
        analytics = {}

        # Find all event files
        for events_file in self.analytics_dir.glob("*_events.jsonl"):
            # Extract project_id from filename
            project_id = events_file.stem.replace("_events", "")
            analytics[project_id] = self.get_analytics(project_id)

        return analytics

    def clear_events(self, project_id: str) -> None:
        """Clear all events for a project.

        Args:
            project_id: Project identifier
        """
        events_file = self._get_events_file(project_id)
        if events_file.exists():
            events_file.unlink()
