"""Screenshot and visual content capture modules."""

from demoforge.capturer.auth import AuthManager, AuthenticatedCapturer
from demoforge.capturer.browser import BrowserCapturer
from demoforge.capturer.fallback import TitleCardGenerator

__all__ = [
    "BrowserCapturer",
    "AuthManager",
    "AuthenticatedCapturer",
    "TitleCardGenerator",
]
