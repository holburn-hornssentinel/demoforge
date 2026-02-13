"""Server-Sent Events (SSE) manager for real-time progress updates."""

import asyncio
import json
from typing import Any
from collections.abc import AsyncGenerator

from sse_starlette.sse import EventSourceResponse

from demoforge.models import PipelineProgress


class SSEManager:
    """Manages Server-Sent Events connections for pipeline progress."""

    def __init__(self) -> None:
        """Initialize SSE manager."""
        self.connections: dict[str, list[asyncio.Queue[PipelineProgress | None]]] = {}

    def add_connection(self, project_id: str) -> asyncio.Queue[PipelineProgress | None]:
        """Add a new SSE connection for a project.

        Args:
            project_id: Project identifier

        Returns:
            Queue for receiving progress updates
        """
        if project_id not in self.connections:
            self.connections[project_id] = []

        queue: asyncio.Queue[PipelineProgress | None] = asyncio.Queue()
        self.connections[project_id].append(queue)
        return queue

    def remove_connection(
        self, project_id: str, queue: asyncio.Queue[PipelineProgress | None]
    ) -> None:
        """Remove an SSE connection.

        Args:
            project_id: Project identifier
            queue: Queue to remove
        """
        if project_id in self.connections:
            try:
                self.connections[project_id].remove(queue)
            except ValueError:
                pass

            # Clean up empty connection lists
            if not self.connections[project_id]:
                del self.connections[project_id]

    async def send_progress(self, project_id: str, progress: PipelineProgress) -> None:
        """Send progress update to all connected clients.

        Args:
            project_id: Project identifier
            progress: Progress update to send
        """
        if project_id in self.connections:
            for queue in self.connections[project_id]:
                await queue.put(progress)

    async def close_connection(self, project_id: str) -> None:
        """Close all connections for a project.

        Args:
            project_id: Project identifier
        """
        if project_id in self.connections:
            for queue in self.connections[project_id]:
                await queue.put(None)  # Sentinel value to close connection


# Global SSE manager instance
sse_manager = SSEManager()


async def progress_stream(
    project_id: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream progress updates for a project.

    Args:
        project_id: Project identifier

    Yields:
        SSE event dictionaries
    """
    queue = sse_manager.add_connection(project_id)

    try:
        while True:
            progress = await queue.get()

            if progress is None:
                # Connection closed
                break

            # Convert progress to SSE event
            yield {
                "event": "progress",
                "data": json.dumps(progress.model_dump(mode="json")),
            }

    finally:
        sse_manager.remove_connection(project_id, queue)


def create_sse_response(project_id: str) -> EventSourceResponse:
    """Create an SSE response for a project.

    Args:
        project_id: Project identifier

    Returns:
        EventSourceResponse for streaming progress
    """
    return EventSourceResponse(progress_stream(project_id))
