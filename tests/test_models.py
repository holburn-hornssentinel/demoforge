"""Tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from demoforge.models import (
    AnalysisResult,
    AudienceType,
    DemoScript,
    Language,
    PipelineStage,
    ProductFeature,
    Scene,
    SceneType,
    TTSEngine,
)


def test_product_feature_validation():
    """Should validate ProductFeature fields."""
    feature = ProductFeature(
        name="AI Analysis",
        description="Analyzes repos using Gemini",
        importance=8,
        demo_worthy=True,
    )

    assert feature.name == "AI Analysis"
    assert feature.importance == 8
    assert feature.demo_worthy is True


def test_product_feature_importance_range():
    """Should enforce importance score range 1-10."""
    # Valid: within range
    ProductFeature(name="Test", description="Test", importance=5, demo_worthy=True)

    # Invalid: below range
    with pytest.raises(ValidationError):
        ProductFeature(name="Test", description="Test", importance=0, demo_worthy=True)

    # Invalid: above range
    with pytest.raises(ValidationError):
        ProductFeature(name="Test", description="Test", importance=11, demo_worthy=True)


def test_analysis_result_defaults():
    """Should use default values for optional fields."""
    analysis = AnalysisResult(
        product_name="TestProduct",
        tagline="Test tagline",
        category="Tool",
    )

    assert analysis.target_users == []
    assert analysis.key_features == []
    assert analysis.tech_stack == []
    assert analysis.use_cases == []
    assert analysis.competitive_advantage == ""
    assert isinstance(analysis.analyzed_at, datetime)


def test_analysis_result_with_urls():
    """Should accept and validate URLs."""
    analysis = AnalysisResult(
        product_name="TestProduct",
        tagline="Test",
        category="Tool",
        github_url="https://github.com/test/repo",
        website_url="https://example.com",
        demo_urls=["https://example.com/demo1", "https://example.com/demo2"],
    )

    # Pydantic HttpUrl normalizes URLs (may add trailing slash)
    assert str(analysis.github_url).rstrip('/') == "https://github.com/test/repo"
    assert str(analysis.website_url).rstrip('/') == "https://example.com"
    assert len(analysis.demo_urls) == 2
    assert all("example.com" in str(url) for url in analysis.demo_urls)


def test_scene_types():
    """Should have all required scene types."""
    assert SceneType.SCREENSHOT == "screenshot"
    assert SceneType.TITLE_CARD == "title_card"
    assert SceneType.CODE_SNIPPET == "code_snippet"
    assert SceneType.DIAGRAM == "diagram"


def test_scene_validation():
    """Should validate Scene fields."""
    scene = Scene(
        id="scene_001",
        scene_type=SceneType.TITLE_CARD,
        narration="Welcome to the demo",
        duration_seconds=5.0,
        visual_content="Welcome Text",
    )

    assert scene.id == "scene_001"
    assert scene.scene_type == SceneType.TITLE_CARD
    assert scene.duration_seconds == 5.0


def test_scene_duration_positive():
    """Should enforce positive duration."""
    # Valid: positive duration
    Scene(
        id="scene_001",
        scene_type=SceneType.TITLE_CARD,
        narration="Test",
        duration_seconds=1.0,
    )

    # Invalid: zero duration
    with pytest.raises(ValidationError):
        Scene(
            id="scene_001",
            scene_type=SceneType.TITLE_CARD,
            narration="Test",
            duration_seconds=0.0,
        )

    # Invalid: negative duration
    with pytest.raises(ValidationError):
        Scene(
            id="scene_001",
            scene_type=SceneType.TITLE_CARD,
            narration="Test",
            duration_seconds=-1.0,
        )


def test_demo_script_language():
    """Should accept language field."""
    script = DemoScript(
        title="Test Demo",
        audience=AudienceType.DEVELOPER,
        language=Language.SPANISH,
        intro="Intro",
        scenes=[
            Scene(
                id="s1",
                scene_type=SceneType.TITLE_CARD,
                narration="Test",
                duration_seconds=5.0,
            )
        ],
        outro="Outro",
        total_duration=5.0,
    )

    assert script.language == Language.SPANISH


def test_language_enum():
    """Should have comprehensive language support."""
    assert Language.ENGLISH == "en"
    assert Language.SPANISH == "es"
    assert Language.FRENCH == "fr"
    assert Language.JAPANESE == "ja"
    assert Language.CHINESE_SIMPLIFIED == "zh-CN"


def test_pipeline_stage_enum():
    """Should have all pipeline stages."""
    assert PipelineStage.ANALYZE == "analyze"
    assert PipelineStage.SCRIPT == "script"
    assert PipelineStage.CAPTURE == "capture"
    assert PipelineStage.VOICE == "voice"
    assert PipelineStage.ASSEMBLE == "assemble"
    assert PipelineStage.COMPLETE == "complete"
    assert PipelineStage.FAILED == "failed"


def test_tts_engine_enum():
    """Should have all TTS engines."""
    assert TTSEngine.KOKORO == "kokoro"
    assert TTSEngine.EDGE == "edge"
    assert TTSEngine.POCKET == "pocket"


def test_audience_type_enum():
    """Should have all audience types."""
    assert AudienceType.INVESTOR == "investor"
    assert AudienceType.CUSTOMER == "customer"
    assert AudienceType.DEVELOPER == "developer"
    assert AudienceType.TECHNICAL == "technical"


def test_demo_script_total_duration():
    """Should store total duration."""
    scenes = [
        Scene(
            id="s1",
            scene_type=SceneType.TITLE_CARD,
            narration="Scene 1",
            duration_seconds=5.0,
        ),
        Scene(
            id="s2",
            scene_type=SceneType.TITLE_CARD,
            narration="Scene 2",
            duration_seconds=7.0,
        ),
    ]

    script = DemoScript(
        title="Test Demo",
        audience=AudienceType.DEVELOPER,
        language=Language.ENGLISH,
        intro="Intro",
        scenes=scenes,
        outro="Outro",
        total_duration=12.0,
    )

    assert script.total_duration == 12.0
    assert len(script.scenes) == 2
