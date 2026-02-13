"""FastAPI dependency functions."""

from demoforge.config import Settings, get_settings

# Global settings instance for dependency injection
_app_settings: Settings | None = None


def get_app_settings() -> Settings:
    """Dependency function to get application settings.

    Returns:
        Application settings
    """
    global _app_settings
    if _app_settings is None:
        _app_settings = get_settings()
    return _app_settings


def set_app_settings(settings: Settings) -> None:
    """Set the global settings instance.

    Args:
        settings: Application settings
    """
    global _app_settings
    _app_settings = settings
