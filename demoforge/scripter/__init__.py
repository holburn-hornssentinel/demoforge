"""Script generation modules for DemoForge.

Generates demo video scripts tailored to different audiences using Claude AI.
"""

from demoforge.scripter.duration import DurationEnforcer
from demoforge.scripter.script_generator import ScriptGenerator

__all__ = ["DurationEnforcer", "ScriptGenerator"]
