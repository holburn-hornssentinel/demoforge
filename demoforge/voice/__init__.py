"""TTS (Text-to-Speech) engines for narration synthesis."""

from pathlib import Path

from demoforge.models import Language, TTSEngine
from demoforge.voice.base import BaseTTSEngine
from demoforge.voice.edge_tts_engine import EdgeTTSEngine
from demoforge.voice.kokoro_tts import KokoroTTSEngine
from demoforge.voice.language_voices import get_voice_for_language, supports_kokoro_tts
from demoforge.voice.pocket_tts import PocketTTSEngine

__all__ = [
    "BaseTTSEngine",
    "KokoroTTSEngine",
    "EdgeTTSEngine",
    "PocketTTSEngine",
    "create_tts_engine",
]


def create_tts_engine(
    engine: TTSEngine = TTSEngine.KOKORO,
    voice: str | None = None,
    speed: float = 1.0,
    output_dir: Path = Path("/app/output/audio"),
    voice_sample_path: Path | None = None,
    language: Language = Language.ENGLISH,
) -> BaseTTSEngine:
    """Factory function to create appropriate TTS engine.

    Args:
        engine: TTS engine type (from TTSEngine enum)
        voice: Voice identifier (engine-specific, uses default if None)
        speed: Speech speed multiplier (0.5 to 2.0)
        output_dir: Directory for generated audio files

    Returns:
        Initialized TTS engine instance

    Raises:
        ValueError: If engine type is unknown or not implemented

    Examples:
        >>> # Create Kokoro engine (local, CPU-based)
        >>> tts = create_tts_engine(TTSEngine.KOKORO, voice="af")
        >>> audio = await tts.synthesize("Hello world", "scene_1")

        >>> # Create Edge TTS engine (cloud-based fallback)
        >>> tts = create_tts_engine(TTSEngine.EDGE, voice="en-US-AriaNeural")
        >>> audio = await tts.synthesize("Hello world", "scene_1")
    """
    if engine == TTSEngine.KOKORO:
        # Auto-fallback to Edge TTS for non-English languages
        if not supports_kokoro_tts(language):
            print(
                f"Warning: Kokoro TTS only supports English. "
                f"Falling back to Edge TTS for {language.value}"
            )
            default_voice = voice or get_voice_for_language(language)
            return EdgeTTSEngine(
                voice=default_voice,
                speed=speed,
                output_dir=output_dir,
            )

        default_voice = voice or "af"  # American Female
        return KokoroTTSEngine(
            voice=default_voice,
            speed=speed,
            output_dir=output_dir,
        )

    elif engine == TTSEngine.EDGE:
        # Use language-appropriate voice if no voice specified
        default_voice = voice or get_voice_for_language(language)
        return EdgeTTSEngine(
            voice=default_voice,
            speed=speed,
            output_dir=output_dir,
        )

    elif engine == TTSEngine.POCKET:
        # Pocket TTS (voice cloning with fallback to Edge TTS)
        default_voice = voice or "en-US-AriaNeural"
        return PocketTTSEngine(
            voice=default_voice,
            speed=speed,
            output_dir=output_dir,
            voice_sample_path=voice_sample_path,
        )

    else:
        raise ValueError(f"Unknown TTS engine: {engine}")
