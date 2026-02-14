"""Video assembly and compositing modules."""

from demoforge.assembler.compositor import VideoCompositor
from demoforge.assembler.overlays import OverlayGenerator
from demoforge.assembler.subtitles import SubtitleGenerator
from demoforge.assembler.transitions import TransitionBuilder, TransitionType

__all__ = [
    "VideoCompositor",
    "OverlayGenerator",
    "SubtitleGenerator",
    "TransitionBuilder",
    "TransitionType",
]
