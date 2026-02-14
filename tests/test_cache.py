"""Tests for pipeline caching system."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from demoforge.cache import PipelineCache
from demoforge.models import PipelineStage


def test_cache_initialization(temp_dir):
    """Should create cache directory on initialization."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True, ttl_hours=72)

    assert cache.cache_dir == temp_dir / "pipeline"
    assert cache.cache_dir.exists()
    assert cache.enabled is True
    assert cache.ttl_hours == 72


def test_cache_set_and_get(temp_dir, sample_cache_hash):
    """Should store and retrieve cached data."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    test_data = {"result": "analysis complete", "features": ["feature1", "feature2"]}

    # Store data
    cache.set(sample_cache_hash, PipelineStage.ANALYZE, test_data)

    # Retrieve data
    cached_data = cache.get(sample_cache_hash, PipelineStage.ANALYZE)

    assert cached_data == test_data
    assert cached_data["result"] == "analysis complete"


def test_cache_get_nonexistent(temp_dir, sample_cache_hash):
    """Should return None for non-existent cache."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    cached_data = cache.get(sample_cache_hash, PipelineStage.ANALYZE)

    assert cached_data is None


def test_cache_disabled(temp_dir, sample_cache_hash):
    """Should not cache when disabled."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=False)

    test_data = {"result": "test"}

    # Try to store data
    cache.set(sample_cache_hash, PipelineStage.ANALYZE, test_data)

    # Should not retrieve (caching disabled)
    cached_data = cache.get(sample_cache_hash, PipelineStage.ANALYZE)

    assert cached_data is None


def test_cache_different_stages(temp_dir, sample_cache_hash):
    """Should store different data for different stages."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    analysis_data = {"stage": "analysis"}
    script_data = {"stage": "script"}

    cache.set(sample_cache_hash, PipelineStage.ANALYZE, analysis_data)
    cache.set(sample_cache_hash, PipelineStage.SCRIPT, script_data)

    retrieved_analysis = cache.get(sample_cache_hash, PipelineStage.ANALYZE)
    retrieved_script = cache.get(sample_cache_hash, PipelineStage.SCRIPT)

    assert retrieved_analysis == analysis_data
    assert retrieved_script == script_data


def test_cache_different_hashes(temp_dir):
    """Should isolate cache entries by hash."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    hash1 = "abc123"
    hash2 = "def456"

    data1 = {"project": "project1"}
    data2 = {"project": "project2"}

    cache.set(hash1, PipelineStage.ANALYZE, data1)
    cache.set(hash2, PipelineStage.ANALYZE, data2)

    assert cache.get(hash1, PipelineStage.ANALYZE) == data1
    assert cache.get(hash2, PipelineStage.ANALYZE) == data2


def test_cache_ttl_expiration(temp_dir, sample_cache_hash):
    """Should expire cache after TTL."""
    # Short TTL for testing (1 second = 1/3600 hours)
    cache = PipelineCache(cache_dir=temp_dir, enabled=True, ttl_hours=1 / 3600)

    test_data = {"result": "test"}
    cache.set(sample_cache_hash, PipelineStage.ANALYZE, test_data)

    # Data should be available immediately
    assert cache.get(sample_cache_hash, PipelineStage.ANALYZE) == test_data

    # Wait for expiration
    time.sleep(2)

    # Data should be expired
    assert cache.get(sample_cache_hash, PipelineStage.ANALYZE) is None


def test_cache_invalid_json(temp_dir, sample_cache_hash):
    """Should handle corrupted cache files."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    # Create invalid cache file manually
    cache_path = cache._get_stage_path(sample_cache_hash, PipelineStage.ANALYZE)
    cache_path.write_text("invalid json content{{{")

    # Should return None and remove invalid file
    result = cache.get(sample_cache_hash, PipelineStage.ANALYZE)

    assert result is None
    assert not cache_path.exists()


def test_cache_invalidate_project(temp_dir, sample_cache_hash):
    """Should invalidate all cache for a project."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    # Store data for multiple stages
    cache.set(sample_cache_hash, PipelineStage.ANALYZE, {"data": "analysis"})
    cache.set(sample_cache_hash, PipelineStage.SCRIPT, {"data": "script"})
    cache.set(sample_cache_hash, PipelineStage.CAPTURE, {"data": "capture"})

    # Invalidate all stages for project
    cache.invalidate(sample_cache_hash)

    assert cache.get(sample_cache_hash, PipelineStage.ANALYZE) is None
    assert cache.get(sample_cache_hash, PipelineStage.SCRIPT) is None
    assert cache.get(sample_cache_hash, PipelineStage.CAPTURE) is None


def test_cache_clear_all(temp_dir):
    """Should clear all cached projects."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    # Create cache for multiple projects
    cache.set("hash1", PipelineStage.ANALYZE, {"project": "1"})
    cache.set("hash2", PipelineStage.ANALYZE, {"project": "2"})
    cache.set("hash3", PipelineStage.ANALYZE, {"project": "3"})

    # Clear all
    removed = cache.clear_all()

    assert removed >= 3
    assert cache.get("hash1", PipelineStage.ANALYZE) is None
    assert cache.get("hash2", PipelineStage.ANALYZE) is None


def test_cache_cleanup_expired(temp_dir):
    """Should remove only expired cache entries."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True, ttl_hours=1)

    # Create fresh cache
    fresh_hash = "fresh123"
    cache.set(fresh_hash, PipelineStage.ANALYZE, {"status": "fresh"})

    # Create expired cache manually (old timestamp)
    expired_hash = "expired456"
    cache_path = cache._get_stage_path(expired_hash, PipelineStage.ANALYZE)
    cache_path.write_text(json.dumps({"stage": "analyze", "output": {"status": "old"}}))

    # Manually set old modification time (3 hours ago)
    old_time = (datetime.now() - timedelta(hours=3)).timestamp()
    cache_path.touch()
    import os

    os.utime(cache_path, (old_time, old_time))

    # Cleanup expired entries
    removed = cache.cleanup_expired()

    # Fresh cache should remain
    assert cache.get(fresh_hash, PipelineStage.ANALYZE) == {"status": "fresh"}

    # Expired cache should be removed
    assert cache.get(expired_hash, PipelineStage.ANALYZE) is None

    assert removed >= 1


def test_cache_get_stats(temp_dir):
    """Should return cache statistics."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    # Create some cache entries
    cache.set("hash1", PipelineStage.ANALYZE, {"data": "1"})
    cache.set("hash1", PipelineStage.SCRIPT, {"data": "2"})
    cache.set("hash2", PipelineStage.ANALYZE, {"data": "3"})

    stats = cache.get_stats()

    assert stats["total_projects"] >= 2
    assert stats["total_stages"] >= 3
    assert stats["enabled"] is True
    assert "ttl_hours" in stats
    assert "total_size_mb" in stats


def test_cache_path_structure(temp_dir, sample_cache_hash):
    """Should create proper directory structure."""
    cache = PipelineCache(cache_dir=temp_dir, enabled=True)

    cache.set(sample_cache_hash, PipelineStage.ANALYZE, {"test": "data"})

    # Check directory structure
    expected_dir = temp_dir / "pipeline" / sample_cache_hash
    expected_file = expected_dir / "analyze.json"

    assert expected_dir.exists()
    assert expected_dir.is_dir()
    assert expected_file.exists()
    assert expected_file.is_file()
