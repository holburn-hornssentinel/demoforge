"""Pipeline caching system for DemoForge.

Provides hash-based caching of pipeline stage outputs to avoid redundant computation.
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from demoforge.models import PipelineStage


class PipelineCache:
    """Manages file-based caching of pipeline stage outputs."""

    def __init__(
        self, cache_dir: Path, enabled: bool = True, ttl_hours: int = 72
    ) -> None:
        """Initialize the pipeline cache.

        Args:
            cache_dir: Base directory for cache storage
            enabled: Whether caching is enabled
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = cache_dir / "pipeline"
        self.enabled = enabled
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_stage_path(self, cache_hash: str, stage: PipelineStage) -> Path:
        """Get the file path for a cached stage output.

        Args:
            cache_hash: Hash identifying the pipeline inputs
            stage: Pipeline stage

        Returns:
            Path to the cache file
        """
        project_cache_dir = self.cache_dir / cache_hash
        project_cache_dir.mkdir(parents=True, exist_ok=True)
        return project_cache_dir / f"{stage.value}.json"

    def get(self, cache_hash: str, stage: PipelineStage) -> Any | None:
        """Retrieve cached output for a pipeline stage.

        Args:
            cache_hash: Hash identifying the pipeline inputs
            stage: Pipeline stage to retrieve

        Returns:
            Cached output data, or None if not found or expired
        """
        if not self.enabled:
            return None

        cache_path = self._get_stage_path(cache_hash, stage)
        if not cache_path.exists():
            return None

        # Check if cache is expired
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age > timedelta(hours=self.ttl_hours):
            # Cache expired, remove it
            cache_path.unlink()
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            return data.get("output")
        except (json.JSONDecodeError, IOError):
            # Invalid cache file, remove it
            cache_path.unlink()
            return None

    def set(self, cache_hash: str, stage: PipelineStage, output: Any) -> None:
        """Store output for a pipeline stage.

        Args:
            cache_hash: Hash identifying the pipeline inputs
            stage: Pipeline stage
            output: Stage output data to cache
        """
        if not self.enabled:
            return

        cache_path = self._get_stage_path(cache_hash, stage)

        data = {
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "output": output,
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except (IOError, TypeError) as e:
            # Log error but don't fail the pipeline
            print(f"Warning: Failed to write cache for {stage.value}: {e}")

    def has(self, cache_hash: str, stage: PipelineStage) -> bool:
        """Check if a valid cache entry exists for a stage.

        Args:
            cache_hash: Hash identifying the pipeline inputs
            stage: Pipeline stage

        Returns:
            True if valid cache exists, False otherwise
        """
        return self.get(cache_hash, stage) is not None

    def invalidate(self, cache_hash: str, stage: PipelineStage | None = None) -> None:
        """Invalidate cache entries.

        Args:
            cache_hash: Hash identifying the pipeline inputs
            stage: Specific stage to invalidate, or None for all stages
        """
        if stage is not None:
            # Invalidate specific stage
            cache_path = self._get_stage_path(cache_hash, stage)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Invalidate all stages for this cache hash
            project_cache_dir = self.cache_dir / cache_hash
            if project_cache_dir.exists():
                shutil.rmtree(project_cache_dir)

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries.

        Returns:
            Number of cache entries removed
        """
        if not self.cache_dir.exists():
            return 0

        removed_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.ttl_hours)

        for project_dir in self.cache_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Check all stage files in this project cache
            all_expired = True
            for cache_file in project_dir.glob("*.json"):
                cache_age = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if cache_age < cutoff_time:
                    cache_file.unlink()
                    removed_count += 1
                else:
                    all_expired = False

            # Remove project directory if all stages are expired
            if all_expired and not list(project_dir.glob("*.json")):
                project_dir.rmdir()

        return removed_count

    def clear_all(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of cache entries removed
        """
        if not self.cache_dir.exists():
            return 0

        count = sum(1 for _ in self.cache_dir.rglob("*.json"))
        shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_dir.exists():
            return {
                "total_projects": 0,
                "total_stages": 0,
                "total_size_mb": 0.0,
                "enabled": self.enabled,
                "ttl_hours": self.ttl_hours,
            }

        total_size = 0
        total_stages = 0
        total_projects = 0

        for project_dir in self.cache_dir.iterdir():
            if not project_dir.is_dir():
                continue

            total_projects += 1
            for cache_file in project_dir.glob("*.json"):
                total_stages += 1
                total_size += cache_file.stat().st_size

        return {
            "total_projects": total_projects,
            "total_stages": total_stages,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "enabled": self.enabled,
            "ttl_hours": self.ttl_hours,
        }
