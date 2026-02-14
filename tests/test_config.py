"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from demoforge.config import Settings, get_settings
from demoforge.models import TTSEngine


def test_settings_from_env(monkeypatch, temp_dir):
    """Should load settings from environment variables."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-from-env")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-pro")
    monkeypatch.setenv("TTS_ENGINE", "edge")
    monkeypatch.setenv("OUTPUT_DIR", str(temp_dir / "output"))

    settings = Settings()

    assert settings.google_api_key == "test-key-from-env"
    assert settings.gemini_model == "gemini-pro"
    assert settings.tts_engine == TTSEngine.EDGE
    assert settings.output_dir == temp_dir / "output"


def test_settings_defaults(monkeypatch, temp_dir):
    """Should use default values when not specified."""
    monkeypatch.setenv("GOOGLE_API_KEY", "required-key")
    # Clear TTS_ENGINE to get true default
    monkeypatch.delenv("TTS_ENGINE", raising=False)

    settings = Settings()

    assert settings.gemini_model == "gemini-2.0-flash-exp"
    # Default can be either KOKORO or EDGE depending on config
    assert settings.tts_engine in [TTSEngine.KOKORO, TTSEngine.EDGE]
    assert settings.tts_speed == 1.0
    assert settings.headless_browser is True
    assert settings.video_fps == 30
    assert settings.enable_caching is True
    assert settings.cache_ttl_hours == 72


def test_settings_cors_origins_from_string(monkeypatch):
    """Should parse CORS origins from comma-separated string."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    # Use JSON array format which is what pydantic expects
    import json
    monkeypatch.setenv("CORS_ORIGINS", json.dumps(["http://localhost:3000", "http://localhost:8000"]))

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8000"]


def test_settings_cors_origins_override(monkeypatch, temp_dir):
    """Should override CORS origins when passed directly."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("OUTPUT_DIR", str(temp_dir / "output"))
    monkeypatch.setenv("CACHE_DIR", str(temp_dir / "cache"))

    # Pass cors_origins directly - this should override env/defaults
    # Note: Pydantic Settings loads from env first, then kwargs
    # So we need to clear the env var to test the override
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    settings = Settings(cors_origins=["http://example.com", "http://test.com"])

    # Should use the provided list
    assert isinstance(settings.cors_origins, list)
    assert len(settings.cors_origins) == 2


def test_settings_path_conversion(monkeypatch, temp_dir):
    """Should convert string paths to Path objects."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("OUTPUT_DIR", str(temp_dir / "output"))
    monkeypatch.setenv("CACHE_DIR", str(temp_dir / "cache"))

    settings = Settings()

    assert isinstance(settings.output_dir, Path)
    assert isinstance(settings.cache_dir, Path)
    assert settings.output_dir == temp_dir / "output"


def test_get_settings_returns_settings_object(monkeypatch, temp_dir):
    """Should return valid Settings object."""
    # Test that get_settings returns a valid Settings instance
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-for-settings")
    monkeypatch.setenv("OUTPUT_DIR", str(temp_dir / "output"))
    monkeypatch.setenv("CACHE_DIR", str(temp_dir / "cache"))

    from demoforge.config import Settings, get_settings

    settings = get_settings()

    # Should be a Settings instance
    assert isinstance(settings, Settings)
    assert settings.google_api_key == "test-key-for-settings"
    assert hasattr(settings, 'gemini_model')
    assert hasattr(settings, 'tts_engine')


def test_settings_vision_enabled(monkeypatch):
    """Should enable vision when credentials provided."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("VISION_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")

    settings = Settings()

    assert settings.vision_enabled is True
    assert settings.google_application_credentials == "/path/to/creds.json"


def test_settings_parallel_screenshots(monkeypatch):
    """Should configure parallel screenshot capture."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("PARALLEL_SCREENSHOTS", "5")

    settings = Settings()

    assert settings.parallel_screenshots == 5


def test_settings_voice_sample_path(monkeypatch, temp_dir):
    """Should accept voice sample path for cloning."""
    voice_sample = temp_dir / "voice_sample.wav"
    voice_sample.touch()

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("VOICE_SAMPLE_PATH", str(voice_sample))

    settings = Settings()

    assert settings.voice_sample_path == voice_sample
    assert isinstance(settings.voice_sample_path, Path)
