"""Core Pydantic models for DemoForge.

These models define the data contracts used throughout the pipeline:
- Analysis results from AI
- Demo script structure
- Scene definitions
- Audio segments
- Pipeline state and progress
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class AudienceType(str, Enum):
    """Target audience for the demo video."""

    INVESTOR = "investor"
    CUSTOMER = "customer"
    DEVELOPER = "developer"
    TECHNICAL = "technical"


class TTSEngine(str, Enum):
    """Text-to-speech engine selection."""

    KOKORO = "kokoro"  # Local, CPU-based, Apache 2.0
    EDGE = "edge"  # Cloud-based, Microsoft
    POCKET = "pocket"  # Voice cloning capable


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    ANALYZE = "analyze"
    SCRIPT = "script"
    CAPTURE = "capture"
    VOICE = "voice"
    ASSEMBLE = "assemble"
    COMPLETE = "complete"
    FAILED = "failed"


class SceneType(str, Enum):
    """Type of scene in the demo."""

    SCREENSHOT = "screenshot"  # Website/app screenshot
    TITLE_CARD = "title_card"  # Text-only title card
    CODE_SNIPPET = "code_snippet"  # Code example
    DIAGRAM = "diagram"  # Architecture diagram


# =============================================================================
# Analysis Models
# =============================================================================


class ProductFeature(BaseModel):
    """A single product feature identified by AI analysis."""

    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Detailed description")
    importance: int = Field(..., ge=1, le=10, description="Importance score (1-10)")
    demo_worthy: bool = Field(..., description="Should this be shown in demo?")


class AnalysisResult(BaseModel):
    """Result of AI-powered product analysis."""

    product_name: str = Field(..., description="Product or project name")
    tagline: str = Field(..., description="One-sentence product description")
    category: str = Field(..., description="Product category (e.g., 'Web framework')")
    target_users: list[str] = Field(
        default_factory=list, description="Target user personas"
    )
    key_features: list[ProductFeature] = Field(
        default_factory=list, description="Key features identified"
    )
    tech_stack: list[str] = Field(default_factory=list, description="Technologies used")
    use_cases: list[str] = Field(default_factory=list, description="Common use cases")
    competitive_advantage: str = Field(
        default="", description="What makes this unique?"
    )
    github_url: HttpUrl | None = Field(None, description="GitHub repository URL")
    website_url: HttpUrl | None = Field(None, description="Product website URL")
    demo_urls: list[HttpUrl] = Field(
        default_factory=list, description="URLs to capture for demo"
    )
    analyzed_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Script Models
# =============================================================================


class SceneAction(BaseModel):
    """Action to perform during a scene (e.g., highlight, zoom)."""

    action_type: str = Field(..., description="Type of action (highlight, zoom, pan)")
    target: str = Field(..., description="CSS selector or coordinate")
    duration_ms: int = Field(default=1000, description="Action duration in ms")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class Scene(BaseModel):
    """A single scene in the demo video."""

    id: str = Field(..., description="Unique scene identifier")
    scene_type: SceneType = Field(..., description="Type of scene")
    narration: str = Field(..., description="Voiceover narration text")
    duration_seconds: float = Field(..., gt=0, description="Scene duration in seconds")
    url: HttpUrl | None = Field(None, description="URL to capture (if screenshot)")
    visual_content: str = Field(
        default="", description="Text content for title cards or code snippets"
    )
    actions: list[SceneAction] = Field(
        default_factory=list, description="Actions during this scene"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional scene metadata"
    )


class DemoScript(BaseModel):
    """Complete demo video script."""

    title: str = Field(..., description="Demo video title")
    audience: AudienceType = Field(..., description="Target audience")
    total_duration: float = Field(..., gt=0, description="Total video length in seconds")
    scenes: list[Scene] = Field(..., min_length=1, description="Ordered list of scenes")
    intro: str = Field(..., description="Opening narration")
    outro: str = Field(..., description="Closing narration")
    call_to_action: str = Field(default="", description="CTA at the end")
    generated_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_words(self) -> int:
        """Calculate total word count for narration."""
        all_text = self.intro + " " + self.outro + " "
        all_text += " ".join(scene.narration for scene in self.scenes)
        return len(all_text.split())

    @property
    def estimated_duration(self) -> float:
        """Estimate duration based on narration (avg 150 words/min)."""
        return (self.total_words / 150.0) * 60.0


# =============================================================================
# Audio Models
# =============================================================================


class AudioSegment(BaseModel):
    """A single audio segment (narration for one scene)."""

    scene_id: str = Field(..., description="Associated scene ID")
    text: str = Field(..., description="Text to synthesize")
    audio_path: Path = Field(..., description="Path to generated audio file")
    duration_seconds: float = Field(..., gt=0, description="Audio duration")
    start_time: float = Field(default=0.0, description="Start time in final video")
    voice_id: str = Field(default="af", description="TTS voice identifier")


class SubtitleEntry(BaseModel):
    """A single subtitle entry (SRT format)."""

    index: int = Field(..., ge=1, description="Subtitle sequence number")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., gt=0, description="End time in seconds")
    text: str = Field(..., description="Subtitle text")


# =============================================================================
# Capture Models
# =============================================================================


class Screenshot(BaseModel):
    """Captured screenshot metadata."""

    scene_id: str = Field(..., description="Associated scene ID")
    url: HttpUrl | None = Field(None, description="URL captured")
    image_path: Path = Field(..., description="Path to screenshot file")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    captured_at: datetime = Field(default_factory=datetime.now)


class AuthCredentials(BaseModel):
    """Authentication credentials for website capture."""

    username: str = Field(..., description="Login username")
    password: str = Field(..., description="Login password")
    login_url: HttpUrl = Field(..., description="Login page URL")
    username_selector: str = Field(
        default='input[type="text"]', description="CSS selector for username field"
    )
    password_selector: str = Field(
        default='input[type="password"]', description="CSS selector for password field"
    )
    submit_selector: str = Field(
        default='button[type="submit"]', description="CSS selector for submit button"
    )


# =============================================================================
# Pipeline Models
# =============================================================================


class PipelineProgress(BaseModel):
    """Real-time pipeline execution progress."""

    stage: PipelineStage = Field(..., description="Current pipeline stage")
    progress: float = Field(..., ge=0, le=1, description="Progress (0.0 to 1.0)")
    message: str = Field(default="", description="Human-readable status message")
    current_scene: int = Field(default=0, description="Current scene being processed")
    total_scenes: int = Field(default=0, description="Total number of scenes")
    error: str | None = Field(None, description="Error message if failed")
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProjectState(BaseModel):
    """Persistent state for a demo project."""

    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Input configuration
    repo_url: HttpUrl | None = Field(None, description="GitHub repository URL")
    website_url: HttpUrl | None = Field(None, description="Website URL")
    audience: AudienceType = Field(
        default=AudienceType.DEVELOPER, description="Target audience"
    )
    target_length: int = Field(default=90, description="Target video length in seconds")

    # Pipeline outputs
    analysis: AnalysisResult | None = None
    script: DemoScript | None = None
    screenshots: list[Screenshot] = Field(default_factory=list)
    audio_segments: list[AudioSegment] = Field(default_factory=list)
    subtitles: list[SubtitleEntry] = Field(default_factory=list)

    # Pipeline state
    current_stage: PipelineStage = Field(default=PipelineStage.ANALYZE)
    progress: PipelineProgress | None = None
    output_path: Path | None = Field(None, description="Final video output path")

    # Caching
    cache_hash: str = Field(default="", description="Hash for cache invalidation")


# =============================================================================
# Configuration Models
# =============================================================================


class TTSConfig(BaseModel):
    """Text-to-speech configuration."""

    engine: TTSEngine = Field(default=TTSEngine.KOKORO, description="TTS engine to use")
    voice: str = Field(default="af", description="Voice ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    voice_sample_path: Path | None = Field(
        None, description="Path to voice sample for cloning"
    )


class BrowserConfig(BaseModel):
    """Browser automation configuration."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout: int = Field(default=30000, description="Page load timeout in ms")
    viewport_width: int = Field(default=2560, description="Viewport width")
    viewport_height: int = Field(default=1440, description="Viewport height")
    auth: AuthCredentials | None = Field(None, description="Authentication credentials")


class VideoConfig(BaseModel):
    """Video assembly configuration."""

    resolution: str = Field(default="1920x1080", description="Output resolution")
    fps: int = Field(default=30, description="Frames per second")
    transition_duration: float = Field(
        default=1.0, description="Crossfade duration in seconds"
    )
    enable_ken_burns: bool = Field(
        default=True, description="Enable Ken Burns pan/zoom effect"
    )
    subtitle_font: str = Field(default="Arial", description="Subtitle font")
    subtitle_size: int = Field(default=24, description="Subtitle font size")


class AppConfig(BaseModel):
    """Application configuration."""

    # API
    google_api_key: str = Field(..., description="Google API key")
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp", description="Gemini model ID"
    )
    vision_enabled: bool = Field(default=False, description="Enable Google Vision API")
    google_application_credentials: str | None = Field(
        None, description="Path to Google service account JSON"
    )

    # TTS
    tts: TTSConfig = Field(default_factory=TTSConfig)

    # Browser
    browser: BrowserConfig = Field(default_factory=BrowserConfig)

    # Video
    video: VideoConfig = Field(default_factory=VideoConfig)

    # Directories
    output_dir: Path = Field(default=Path("/app/output"), description="Output directory")
    cache_dir: Path = Field(default=Path("/app/cache"), description="Cache directory")

    # Pipeline
    enable_caching: bool = Field(default=True, description="Enable pipeline caching")
    parallel_screenshots: int = Field(
        default=3, description="Number of parallel screenshot captures"
    )
    max_video_length: int = Field(
        default=300, description="Maximum video length in seconds"
    )
