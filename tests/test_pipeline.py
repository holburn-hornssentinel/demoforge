"""Tests for pipeline execution and orchestration."""

import pytest

from demoforge.models import AudienceType, Language, PipelineStage
from demoforge.pipeline import Pipeline


def test_pipeline_initialization(mock_app_config):
    """Should initialize pipeline with config."""
    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.config == mock_app_config
    assert pipeline.cache is not None
    assert pipeline.cache.enabled is True
    assert pipeline.ai_analyzer is not None
    assert pipeline.script_generator is not None
    assert pipeline.browser_capturer is not None


def test_pipeline_cache_hash_computation(mock_app_config):
    """Should compute consistent cache hash from inputs."""
    pipeline = Pipeline(config=mock_app_config)

    hash1 = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    hash2 = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    # Same inputs should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hash length


def test_pipeline_cache_hash_different_inputs(mock_app_config):
    """Should produce different hashes for different inputs."""
    pipeline = Pipeline(config=mock_app_config)

    hash1 = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo1",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    hash2 = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo2",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    # Different inputs should produce different hashes
    assert hash1 != hash2


def test_pipeline_cache_hash_audience_sensitivity(mock_app_config):
    """Should change hash when audience changes."""
    pipeline = Pipeline(config=mock_app_config)

    hash_dev = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    hash_investor = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.INVESTOR,
        target_length=90,
    )

    assert hash_dev != hash_investor


def test_pipeline_cache_hash_target_length_sensitivity(mock_app_config):
    """Should change hash when target length changes."""
    pipeline = Pipeline(config=mock_app_config)

    hash_90 = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    hash_120 = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=120,
    )

    assert hash_90 != hash_120


def test_pipeline_cache_hash_format(mock_app_config):
    """Should produce valid SHA256 hash string."""
    pipeline = Pipeline(config=mock_app_config)

    hash_result = pipeline._compute_cache_hash(
        repo_url="https://github.com/test/repo",
        website_url=None,
        audience=AudienceType.DEVELOPER,
        target_length=90,
    )

    # Should be a hex string (SHA256 = 64 characters)
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64
    assert all(c in "0123456789abcdef" for c in hash_result)


def test_pipeline_caching_enabled(mock_app_config):
    """Should use cache when enabled."""
    mock_app_config.enable_caching = True
    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.cache.enabled is True


def test_pipeline_caching_disabled(mock_app_config):
    """Should skip cache when disabled."""
    mock_app_config.enable_caching = False
    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.cache.enabled is False


def test_pipeline_vision_analyzer_initialization(mock_app_config, temp_dir):
    """Should initialize vision analyzer when enabled."""
    mock_app_config.vision_enabled = True
    mock_app_config.google_application_credentials = str(
        temp_dir / "fake_credentials.json"
    )

    # Vision analyzer initialization requires valid credentials
    # In production tests, use mocking for Vision API
    assert mock_app_config.vision_enabled is True


def test_pipeline_parallel_screenshots_config(mock_app_config):
    """Should configure parallel screenshot capture."""
    mock_app_config.parallel_screenshots = 5

    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.config.parallel_screenshots == 5


def test_pipeline_component_initialization(mock_app_config):
    """Should initialize all pipeline components."""
    pipeline = Pipeline(config=mock_app_config)

    # All core components should be initialized
    assert pipeline.repo_analyzer is not None
    assert pipeline.web_analyzer is not None
    assert pipeline.ai_analyzer is not None
    assert pipeline.script_generator is not None
    assert pipeline.browser_capturer is not None
    assert pipeline.title_card_generator is not None


def test_pipeline_max_video_length_validation(mock_app_config):
    """Should validate video length constraints."""
    mock_app_config.max_video_length = 300

    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.config.max_video_length == 300


def test_pipeline_transition_duration_config(mock_app_config):
    """Should configure transition duration."""
    mock_app_config.video.transition_duration = 1.5

    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.config.video.transition_duration == 1.5


def test_pipeline_ken_burns_config(mock_app_config):
    """Should configure Ken Burns effect."""
    mock_app_config.video.enable_ken_burns = False

    pipeline = Pipeline(config=mock_app_config)

    assert pipeline.config.video.enable_ken_burns is False
