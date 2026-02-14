"""Edge TTS engine - cloud-based Microsoft TTS.

Edge TTS provides excellent quality neural voices for free.
NOTE: This is intended as a fallback and for prototyping.
Review Microsoft's Terms of Service for production use.

GitHub: https://github.com/rany2/edge-tts
"""

import asyncio
from datetime import datetime
from pathlib import Path

import edge_tts

from demoforge.models import AudioSegment
from demoforge.voice.base import BaseTTSEngine


class EdgeTTSEngine(BaseTTSEngine):
    """Edge TTS cloud-based engine.

    Provides high-quality neural voices via Microsoft Edge TTS API.
    No API key required, but review TOS for production use.
    """

    # Popular English voices
    DEFAULT_VOICES = {
        "en-US-AriaNeural": "Female, American, Conversational",
        "en-US-GuyNeural": "Male, American, Conversational",
        "en-GB-SoniaNeural": "Female, British, Professional",
        "en-GB-RyanNeural": "Male, British, Professional",
        "en-US-JennyNeural": "Female, American, Friendly",
        "en-US-EricNeural": "Male, American, Professional",
    }

    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
        output_dir: Path = Path("/app/output/audio"),
    ) -> None:
        """Initialize Edge TTS engine.

        Args:
            voice: Voice name (e.g., 'en-US-AriaNeural')
            speed: Speech speed multiplier (0.5 to 2.0)
            output_dir: Directory for audio files
        """
        super().__init__(voice, speed, output_dir)
        self._available_voices = None

    async def synthesize(
        self,
        text: str,
        scene_id: str,
        voice: str | None = None,
    ) -> AudioSegment:
        """Synthesize speech using Edge TTS.

        Args:
            text: Text to synthesize
            scene_id: Scene identifier
            voice: Voice override

        Returns:
            AudioSegment with audio file and metadata
        """
        voice_name = voice or self.voice

        # Generate filename
        safe_id = self._sanitize_filename(scene_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_id}_{timestamp}.mp3"
        audio_path = self.output_dir / filename

        # Create Edge TTS communicator
        # Rate: adjust speed (-50% to +100%)
        rate_percent = int((self.speed - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%"

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_name,
            rate=rate_str,
        )

        # Save audio file
        await communicate.save(str(audio_path))

        # Get audio duration using edge_tts metadata
        duration_seconds = await self._get_audio_duration(audio_path)

        return AudioSegment(
            scene_id=scene_id,
            text=text,
            audio_path=audio_path,
            duration_seconds=duration_seconds,
            start_time=0.0,
            voice_id=voice_name,
        )

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get actual audio file duration.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        try:
            # Try using ffprobe (most accurate)
            import subprocess

            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                return float(result.stdout.strip())

        except (FileNotFoundError, ValueError):
            pass

        # Fallback: estimate from file size (rough approximation)
        # MP3 at 128kbps ≈ 16KB/sec
        file_size = audio_path.stat().st_size
        return file_size / 16000.0

    async def get_available_voices(self) -> list[str]:
        """Get list of all available Edge TTS voices.

        Returns:
            List of voice names
        """
        if self._available_voices is None:
            voices = await edge_tts.list_voices()
            self._available_voices = [v["Name"] for v in voices]

        return self._available_voices

    async def estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on word count.

        Args:
            text: Text to estimate

        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        # Average speaking rate: 150 words/min = 2.5 words/sec
        base_duration = word_count / 2.5
        # Adjust for speed
        return base_duration / self.speed

    @classmethod
    async def list_voices_by_language(cls, language_code: str = "en") -> dict[str, str]:
        """List available voices filtered by language.

        Args:
            language_code: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            Dict mapping voice name to description
        """
        all_voices = await edge_tts.list_voices()
        filtered = {}

        for voice in all_voices:
            name = voice["Name"]
            if name.startswith(f"{language_code}-"):
                locale = voice["Locale"]
                gender = voice["Gender"]
                filtered[name] = f"{gender}, {locale}"

        return filtered
