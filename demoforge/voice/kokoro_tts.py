"""Kokoro TTS engine - local, CPU-based, Apache 2.0 licensed.

Kokoro is an 82M parameter TTS model that runs 3-11x realtime on CPU.
Paper: https://arxiv.org/abs/2410.02792
License: Apache 2.0 (commercial use allowed)
"""

import asyncio
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

from demoforge.models import AudioSegment
from demoforge.voice.base import BaseTTSEngine


class KokoroTTSEngine(BaseTTSEngine):
    """Kokoro TTS engine with lazy model loading.

    Supports voices: af (American Female), am (American Male),
                     bf (British Female), bm (British Male)
    """

    # Supported voices
    VOICES = {
        "af": "af_bella",  # American Female - Bella
        "am": "am_adam",  # American Male - Adam
        "bf": "bf_emma",  # British Female - Emma
        "bm": "bm_george",  # British Male - George
    }

    def __init__(
        self,
        voice: str = "af",
        speed: float = 1.0,
        output_dir: Path = Path("/app/output/audio"),
        sample_rate: int = 24000,
    ) -> None:
        """Initialize Kokoro TTS engine.

        Args:
            voice: Voice ID (af, am, bf, bm)
            speed: Speech speed multiplier
            output_dir: Directory for audio files
            sample_rate: Audio sample rate in Hz
        """
        super().__init__(voice, speed, output_dir)
        self.sample_rate = sample_rate
        self._pipeline = None
        self._model_loaded = False

    async def _get_pipeline(self):
        """Lazy load Kokoro pipeline.

        Defers loading the ~300MB model until first synthesis call.
        This prevents slowing down CLI startup for non-TTS commands.

        Returns:
            Kokoro TTS instance

        Raises:
            FileNotFoundError: If model files not found
        """
        if self._pipeline is None:
            # Import only when needed (lazy loading)
            try:
                from kokoro_onnx import Kokoro
            except ImportError as e:
                msg = (
                    "Kokoro TTS not installed. "
                    "Install with: pip install kokoro-onnx"
                )
                raise ImportError(msg) from e

            # Model paths (needs to be downloaded separately)
            # TODO: Add model download utility or document where to get models
            model_path = "/app/cache/kokoro/kokoro-v0_19.onnx"
            voices_path = "/app/cache/kokoro/voices.bin"

            # Check if models exist
            if not Path(model_path).exists() or not Path(voices_path).exists():
                raise FileNotFoundError(
                    "Kokoro models not found. "
                    "Please download models from: "
                    "https://github.com/thewh1teagle/kokoro-onnx/releases "
                    f"Expected paths: {model_path}, {voices_path}"
                )

            # Load model in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            self._pipeline = await loop.run_in_executor(
                None,
                lambda: Kokoro(model_path=model_path, voices_path=voices_path),
            )
            self._model_loaded = True

        return self._pipeline

    async def synthesize(
        self,
        text: str,
        scene_id: str,
        voice: str | None = None,
    ) -> AudioSegment:
        """Synthesize speech using Kokoro.

        Args:
            text: Text to synthesize
            scene_id: Scene identifier
            voice: Voice override (af, am, bf, bm)

        Returns:
            AudioSegment with audio file path and metadata
        """
        voice_id = voice or self.voice
        if voice_id not in self.VOICES:
            raise ValueError(
                f"Invalid voice '{voice_id}'. "
                f"Available: {list(self.VOICES.keys())}"
            )

        # Get pipeline (lazy load on first call)
        pipeline = await self._get_pipeline()

        # Generate filename
        safe_id = self._sanitize_filename(scene_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_id}_{timestamp}.wav"
        audio_path = self.output_dir / filename

        # Synthesize audio in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            pipeline,
            text,
            voice_id,
        )

        # Apply speed adjustment if needed
        if self.speed != 1.0:
            audio_data = self._adjust_speed(audio_data, self.speed)

        # Save audio file
        await loop.run_in_executor(
            None,
            sf.write,
            str(audio_path),
            audio_data,
            self.sample_rate,
        )

        # Calculate actual duration
        duration_seconds = len(audio_data) / self.sample_rate

        return AudioSegment(
            scene_id=scene_id,
            text=text,
            audio_path=audio_path,
            duration_seconds=duration_seconds,
            start_time=0.0,  # Will be set during assembly
            voice_id=voice_id,
        )

    def _synthesize_sync(self, pipeline, text: str, voice_id: str) -> np.ndarray:
        """Synchronous synthesis (runs in thread pool).

        Args:
            pipeline: Kokoro instance
            text: Text to synthesize
            voice_id: Voice identifier

        Returns:
            Audio samples as numpy array
        """
        voice_name = self.VOICES[voice_id]

        # Generate audio samples using kokoro_onnx API
        # The Kokoro class has a create method that returns audio data
        audio_data = pipeline.create(
            text=text,
            voice=voice_name,
            speed=self.speed,
        )

        # Ensure we have valid audio data
        if audio_data is None or len(audio_data) == 0:
            # Empty audio (shouldn't happen, but handle gracefully)
            audio_data = np.zeros(100, dtype=np.float32)

        return audio_data

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Adjust audio playback speed using resampling.

        Args:
            audio: Audio samples
            speed: Speed multiplier (>1.0 = faster, <1.0 = slower)

        Returns:
            Speed-adjusted audio samples
        """
        try:
            from scipy import signal
        except ImportError:
            # Fallback: just return original if scipy not available
            return audio

        # Calculate new length
        new_length = int(len(audio) / speed)

        # Resample using polyphase filtering
        audio_resampled = signal.resample(audio, new_length)

        return audio_resampled.astype(np.float32)

    async def get_available_voices(self) -> list[str]:
        """Get list of available Kokoro voices.

        Returns:
            List of voice IDs
        """
        return list(self.VOICES.keys())

    async def estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on word count.

        Uses average speaking rate of 150 words/minute.

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
