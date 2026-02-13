"""Configuration management for DemoForge.

Loads configuration from multiple sources with priority:
1. Environment variables (highest priority)
2. YAML config file (demoforge.yml)
3. Defaults (lowest priority)
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from demoforge.models import (
    AppConfig,
    BrowserConfig,
    TTSConfig,
    TTSEngine,
    VideoConfig,
)


class Settings(BaseSettings):
    """Application settings loaded from environment and config files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: str = Field(..., validation_alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(
        default="claude-sonnet-4-5-20250929", validation_alias="CLAUDE_MODEL"
    )

    # TTS Configuration
    tts_engine: TTSEngine = Field(default=TTSEngine.KOKORO, validation_alias="TTS_ENGINE")
    tts_voice: str = Field(default="af", validation_alias="TTS_VOICE")
    tts_speed: float = Field(default=1.0, validation_alias="TTS_SPEED")
    voice_sample_path: Path | None = Field(None, validation_alias="VOICE_SAMPLE_PATH")

    # Browser Configuration
    headless_browser: bool = Field(default=True, validation_alias="HEADLESS_BROWSER")
    browser_timeout: int = Field(default=30000, validation_alias="BROWSER_TIMEOUT")
    screenshot_resolution: str = Field(
        default="2560x1440", validation_alias="SCREENSHOT_RESOLUTION"
    )

    # Video Configuration
    video_resolution: str = Field(default="1920x1080", validation_alias="VIDEO_RESOLUTION")
    video_fps: int = Field(default=30, validation_alias="VIDEO_FPS")
    transition_duration: float = Field(
        default=1.0, validation_alias="TRANSITION_DURATION"
    )
    enable_ken_burns: bool = Field(default=True, validation_alias="ENABLE_KEN_BURNS")
    subtitle_font: str = Field(default="Arial", validation_alias="SUBTITLE_FONT")
    subtitle_size: int = Field(default=24, validation_alias="SUBTITLE_SIZE")

    # Directories
    output_dir: Path = Field(default=Path("/app/output"), validation_alias="OUTPUT_DIR")
    cache_dir: Path = Field(default=Path("/app/cache"), validation_alias="CACHE_DIR")

    # Pipeline Settings
    enable_caching: bool = Field(default=True, validation_alias="ENABLE_CACHING")
    parallel_screenshots: int = Field(
        default=3, validation_alias="PARALLEL_SCREENSHOTS"
    )
    max_video_length: int = Field(default=300, validation_alias="MAX_VIDEO_LENGTH")

    # Server Settings
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=7500, validation_alias="API_PORT")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:7501", "http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )

    def to_app_config(self) -> AppConfig:
        """Convert Settings to AppConfig model."""
        # Parse screenshot resolution
        screenshot_width, screenshot_height = map(
            int, self.screenshot_resolution.split("x")
        )

        return AppConfig(
            anthropic_api_key=self.anthropic_api_key,
            claude_model=self.claude_model,
            tts=TTSConfig(
                engine=self.tts_engine,
                voice=self.tts_voice,
                speed=self.tts_speed,
                voice_sample_path=self.voice_sample_path,
            ),
            browser=BrowserConfig(
                headless=self.headless_browser,
                timeout=self.browser_timeout,
                viewport_width=screenshot_width,
                viewport_height=screenshot_height,
            ),
            video=VideoConfig(
                resolution=self.video_resolution,
                fps=self.video_fps,
                transition_duration=self.transition_duration,
                enable_ken_burns=self.enable_ken_burns,
                subtitle_font=self.subtitle_font,
                subtitle_size=self.subtitle_size,
            ),
            output_dir=self.output_dir,
            cache_dir=self.cache_dir,
            enable_caching=self.enable_caching,
            parallel_screenshots=self.parallel_screenshots,
            max_video_length=self.max_video_length,
        )


def load_yaml_config(config_path: Path = Path("demoforge.yml")) -> dict[str, Any]:
    """Load configuration from YAML file if it exists.

    Args:
        config_path: Path to YAML config file

    Returns:
        Configuration dictionary, or empty dict if file doesn't exist
    """
    if not config_path.exists():
        return {}

    with open(config_path) as f:
        config = yaml.safe_load(f)

    return config or {}


def merge_yaml_config(settings: Settings, yaml_config: dict[str, Any]) -> None:
    """Merge YAML configuration into Settings (only if env var not set).

    Args:
        settings: Settings instance to update
        yaml_config: YAML configuration dictionary
    """
    # API configuration
    if "api" in yaml_config:
        if "anthropic_key" in yaml_config["api"]:
            settings.anthropic_api_key = yaml_config["api"]["anthropic_key"]
        if "claude_model" in yaml_config["api"]:
            settings.claude_model = yaml_config["api"]["claude_model"]

    # TTS configuration
    if "tts" in yaml_config:
        if "engine" in yaml_config["tts"]:
            settings.tts_engine = TTSEngine(yaml_config["tts"]["engine"])
        if "voice" in yaml_config["tts"]:
            settings.tts_voice = yaml_config["tts"]["voice"]
        if "speed" in yaml_config["tts"]:
            settings.tts_speed = yaml_config["tts"]["speed"]
        if "voice_sample_path" in yaml_config["tts"]:
            settings.voice_sample_path = Path(yaml_config["tts"]["voice_sample_path"])

    # Browser configuration
    if "browser" in yaml_config:
        if "headless" in yaml_config["browser"]:
            settings.headless_browser = yaml_config["browser"]["headless"]
        if "timeout" in yaml_config["browser"]:
            settings.browser_timeout = yaml_config["browser"]["timeout"]
        if "resolution" in yaml_config["browser"]:
            settings.screenshot_resolution = yaml_config["browser"]["resolution"]

    # Video configuration
    if "video" in yaml_config:
        if "resolution" in yaml_config["video"]:
            settings.video_resolution = yaml_config["video"]["resolution"]
        if "fps" in yaml_config["video"]:
            settings.video_fps = yaml_config["video"]["fps"]
        if "transition_duration" in yaml_config["video"]:
            settings.transition_duration = yaml_config["video"]["transition_duration"]
        if "enable_ken_burns" in yaml_config["video"]:
            settings.enable_ken_burns = yaml_config["video"]["enable_ken_burns"]

    # Output configuration
    if "output" in yaml_config:
        if "dir" in yaml_config["output"]:
            settings.output_dir = Path(yaml_config["output"]["dir"])
        if "cache_dir" in yaml_config["output"]:
            settings.cache_dir = Path(yaml_config["output"]["cache_dir"])
        if "max_length" in yaml_config["output"]:
            settings.max_video_length = yaml_config["output"]["max_length"]

    # Pipeline configuration
    if "pipeline" in yaml_config:
        if "enable_caching" in yaml_config["pipeline"]:
            settings.enable_caching = yaml_config["pipeline"]["enable_caching"]
        if "parallel_screenshots" in yaml_config["pipeline"]:
            settings.parallel_screenshots = yaml_config["pipeline"][
                "parallel_screenshots"
            ]


def get_settings(config_path: Path | None = None) -> Settings:
    """Get application settings from all sources.

    Priority order:
    1. Environment variables (highest)
    2. YAML config file
    3. Defaults (lowest)

    Args:
        config_path: Optional path to YAML config file

    Returns:
        Merged Settings instance
    """
    # Load from environment variables first
    settings = Settings()

    # Load and merge YAML config if provided
    if config_path is None:
        config_path = Path("demoforge.yml")

    yaml_config = load_yaml_config(config_path)
    if yaml_config:
        merge_yaml_config(settings, yaml_config)

    # Ensure output directories exist
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)

    return settings


# Global settings instance (lazy-loaded)
_settings: Settings | None = None


def get_cached_settings() -> Settings:
    """Get cached settings instance (singleton pattern).

    Returns:
        Cached Settings instance
    """
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def reload_settings(config_path: Path | None = None) -> Settings:
    """Reload settings from all sources.

    Args:
        config_path: Optional path to YAML config file

    Returns:
        Fresh Settings instance
    """
    global _settings
    _settings = get_settings(config_path)
    return _settings
