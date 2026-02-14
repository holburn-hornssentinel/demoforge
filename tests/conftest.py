"""Pytest fixtures and configuration for DemoForge tests.

Provides reusable fixtures for mocking settings, sample data, and test clients.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from demoforge.config import Settings
from demoforge.models import (
    AnalysisResult,
    AppConfig,
    AudienceType,
    BrowserConfig,
    DemoScript,
    Language,
    PipelineStage,
    ProductFeature,
    Scene,
    SceneType,
    TTSConfig,
    TTSEngine,
    VideoConfig,
)
from demoforge.server.app import create_app


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_app_config(temp_dir: Path) -> AppConfig:
    """Create mock AppConfig for testing.

    Args:
        temp_dir: Temporary directory for outputs

    Returns:
        AppConfig instance with test configuration
    """
    return AppConfig(
        google_api_key="test-api-key-123",
        gemini_model="gemini-2.0-flash-exp",
        vision_enabled=False,
        google_application_credentials=None,
        tts=TTSConfig(
            engine=TTSEngine.KOKORO,
            voice="af",
            speed=1.0,
            voice_sample_path=None,
        ),
        browser=BrowserConfig(
            headless=True,
            timeout=30000,
            viewport_width=2560,
            viewport_height=1440,
            auth=None,
        ),
        video=VideoConfig(
            resolution="1920x1080",
            fps=30,
            transition_duration=1.0,
            enable_ken_burns=True,
            subtitle_font="Arial",
            subtitle_size=24,
        ),
        output_dir=temp_dir / "output",
        cache_dir=temp_dir / "cache",
        enable_caching=True,
        cache_ttl_hours=72,
        parallel_screenshots=3,
        max_video_length=300,
    )


@pytest.fixture
def mock_settings(temp_dir: Path) -> Settings:
    """Create mock settings for testing.

    Args:
        temp_dir: Temporary directory for outputs

    Returns:
        Settings instance with test configuration
    """
    return Settings(
        google_api_key="test-api-key-123",
        gemini_model="gemini-2.0-flash-exp",
        vision_enabled=False,
        google_application_credentials=None,
        tts_engine=TTSEngine.KOKORO,
        tts_voice="af",
        tts_speed=1.0,
        voice_sample_path=None,
        headless_browser=True,
        browser_timeout=30000,
        screenshot_resolution="1920x1080",
        video_resolution="1920x1080",
        video_fps=30,
        transition_duration=1.0,
        enable_ken_burns=True,
        subtitle_font="Arial",
        subtitle_size=24,
        output_dir=temp_dir / "output",
        cache_dir=temp_dir / "cache",
        enable_caching=True,
        cache_ttl_hours=72,
        default_language="en",
        brand_config_path=None,
        parallel_screenshots=3,
        max_video_length=300,
        api_host="0.0.0.0",
        api_port=7500,
        cors_origins=["http://localhost:7501"],
    )


@pytest.fixture
def sample_analysis() -> AnalysisResult:
    """Create a sample analysis result for testing.

    Returns:
        AnalysisResult with mock data
    """
    return AnalysisResult(
        product_name="DemoForge",
        tagline="Automated product demo video generator",
        category="DevOps Tool",
        target_users=["Developers", "Product Managers", "Marketing Teams"],
        key_features=[
            ProductFeature(
                name="AI Analysis",
                description="Analyzes product repos and websites using Gemini",
                importance=10,
                demo_worthy=True,
            ),
            ProductFeature(
                name="Automated Capture",
                description="Screenshots websites using Playwright",
                importance=9,
                demo_worthy=True,
            ),
            ProductFeature(
                name="Voice Generation",
                description="TTS narration with Kokoro and Edge TTS",
                importance=8,
                demo_worthy=True,
            ),
        ],
        tech_stack=["Python", "FastAPI", "React", "Playwright", "FFmpeg"],
        use_cases=[
            "Generate product demos for GitHub releases",
            "Create marketing videos from documentation",
            "Automate demo creation for CI/CD",
        ],
        competitive_advantage="Fully automated, AI-driven video generation",
        github_url="https://github.com/example/demoforge",
        website_url="https://demoforge.example.com",
        demo_urls=[
            "https://demoforge.example.com",
            "https://demoforge.example.com/features",
        ],
        analyzed_at=datetime(2026, 2, 13, 12, 0, 0),
    )


@pytest.fixture
def sample_script() -> DemoScript:
    """Create a sample demo script for testing.

    Returns:
        DemoScript with sample scenes
    """
    return DemoScript(
        title="DemoForge: Automated Demo Video Generator",
        audience=AudienceType.DEVELOPER,
        language=Language.ENGLISH,
        intro="Welcome to DemoForge: Automated product demo video generator",
        scenes=[
            Scene(
                id="scene_001",
                scene_type=SceneType.TITLE_CARD,
                narration="DemoForge automates the creation of professional product demos",
                duration_seconds=5.0,
                visual_content="DemoForge\nAutomated Demo Videos",
            ),
            Scene(
                id="scene_002",
                scene_type=SceneType.SCREENSHOT,
                narration="The AI analyzes your product repository and website",
                duration_seconds=7.0,
                url="https://github.com/example/demoforge",
            ),
            Scene(
                id="scene_003",
                scene_type=SceneType.SCREENSHOT,
                narration="Then generates a complete demo script with narration",
                duration_seconds=6.0,
                url="https://demoforge.example.com/features",
            ),
            Scene(
                id="scene_004",
                scene_type=SceneType.DIAGRAM,
                narration="The pipeline captures screenshots, generates voice, and assembles the final video",
                duration_seconds=8.0,
                visual_content="Analyze → Script → Capture → Voice → Assemble",
            ),
        ],
        outro="Try DemoForge today at github.com/example/demoforge",
        total_duration=26.0,
        call_to_action="Visit github.com/example/demoforge to get started",
        generated_at=datetime(2026, 2, 13, 12, 5, 0),
    )


@pytest.fixture
def app_client(mock_settings: Settings, temp_dir: Path) -> TestClient:
    """Create FastAPI test client.

    Args:
        mock_settings: Mock settings for the app
        temp_dir: Temporary directory for test data

    Returns:
        TestClient for making API requests
    """
    # Override cache and output dirs to use temp_dir with proper permissions
    mock_settings.cache_dir = temp_dir / "cache"
    mock_settings.output_dir = temp_dir / "output"
    mock_settings.cache_dir.mkdir(parents=True, exist_ok=True)
    mock_settings.output_dir.mkdir(parents=True, exist_ok=True)

    app = create_app(mock_settings)
    return TestClient(app)


@pytest.fixture
def sample_cache_hash() -> str:
    """Sample cache hash for testing.

    Returns:
        SHA256 hash string
    """
    return "abc123def456789012345678901234567890123456789012345678901234"


@pytest.fixture
def sample_pipeline_stages() -> list[PipelineStage]:
    """List of pipeline stages for testing.

    Returns:
        List of PipelineStage enum values
    """
    return [
        PipelineStage.ANALYZE,
        PipelineStage.SCRIPT,
        PipelineStage.CAPTURE,
        PipelineStage.VOICE,
        PipelineStage.ASSEMBLE,
    ]
