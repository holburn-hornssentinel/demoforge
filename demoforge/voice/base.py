"""Abstract base class for TTS (Text-to-Speech) engines."""

from abc import ABC, abstractmethod
from pathlib import Path

from demoforge.models import AudioSegment


class BaseTTSEngine(ABC):
    """Abstract base class for all TTS engines.

    All TTS implementations (Kokoro, Edge, Pocket) inherit from this.
    """

    def __init__(
        self,
        voice: str = "af",
        speed: float = 1.0,
        output_dir: Path = Path("/app/output/audio"),
    ) -> None:
        """Initialize TTS engine.

        Args:
            voice: Voice identifier (engine-specific)
            speed: Speech speed multiplier (0.5 to 2.0)
            output_dir: Directory to save generated audio files
        """
        self.voice = voice
        self.speed = speed
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        scene_id: str,
        voice: str | None = None,
    ) -> AudioSegment:
        """Synthesize speech from text.

        Args:
            text: Text to convert to speech
            scene_id: Scene identifier for filename generation
            voice: Optional voice override (uses self.voice if None)

        Returns:
            AudioSegment with path to generated audio file and metadata

        Raises:
            Exception: If synthesis fails
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[str]:
        """Get list of available voice IDs.

        Returns:
            List of voice identifier strings
        """
        pass

    @abstractmethod
    async def estimate_duration(self, text: str) -> float:
        """Estimate audio duration for given text.

        Args:
            text: Text to estimate

        Returns:
            Estimated duration in seconds
        """
        pass

    async def synthesize_multiple(
        self,
        segments: list[tuple[str, str]],
    ) -> list[AudioSegment]:
        """Synthesize multiple text segments.

        Args:
            segments: List of (scene_id, text) tuples

        Returns:
            List of AudioSegment objects
        """
        results = []
        for scene_id, text in segments:
            audio_segment = await self.synthesize(text, scene_id)
            results.append(audio_segment)
        return results

    def _sanitize_filename(self, scene_id: str) -> str:
        """Sanitize scene_id for use in filename.

        Args:
            scene_id: Scene identifier

        Returns:
            Safe filename component
        """
        # Remove or replace unsafe characters
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in scene_id)
        return safe_id[:100]  # Limit length
