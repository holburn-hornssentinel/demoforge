"""Video compositor using FFmpeg for final MP4 assembly.

Handles scene clip creation, Ken Burns effects, audio sync, transitions,
and subtitle burning to produce professional demo videos.
"""

import subprocess
from pathlib import Path
from typing import Callable

from demoforge.assembler.transitions import TransitionBuilder, TransitionType
from demoforge.models import AudioSegment, Screenshot


class VideoCompositor:
    """Assembles final video from screenshots, audio, and subtitles."""

    def __init__(
        self,
        output_dir: Path = Path("/app/output"),
        fps: int = 30,
        resolution: str = "1920x1080",
        enable_ken_burns: bool = True,
        transition_duration: float = 1.0,
        transition_type: TransitionType = TransitionType.FADE,
    ) -> None:
        """Initialize video compositor.

        Args:
            output_dir: Directory for output videos
            fps: Frames per second
            resolution: Output resolution (WxH)
            enable_ken_burns: Enable Ken Burns pan/zoom effect
            transition_duration: Duration of scene transitions
            transition_type: Type of transition effect
        """
        self.output_dir = output_dir
        self.fps = fps
        self.resolution = resolution
        self.enable_ken_burns = enable_ken_burns
        self.transition_duration = transition_duration
        self.transition_type = transition_type

        # Parse resolution
        self.width, self.height = map(int, resolution.split("x"))

        # Initialize transition builder
        self.transition_builder = TransitionBuilder(
            default_transition=transition_type,
            default_duration=transition_duration,
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_scene_clip(
        self,
        screenshot: Screenshot,
        audio: AudioSegment,
        output_path: Path,
        enable_ken_burns: bool | None = None,
    ) -> Path:
        """Create a single scene video clip from image and audio.

        Args:
            screenshot: Screenshot to use as visual
            audio: Audio narration for this scene
            output_path: Path to save the clip
            enable_ken_burns: Override Ken Burns setting for this clip

        Returns:
            Path to created video clip

        Raises:
            subprocess.CalledProcessError: If FFmpeg fails
        """
        use_ken_burns = (
            enable_ken_burns
            if enable_ken_burns is not None
            else self.enable_ken_burns
        )

        duration = audio.duration_seconds

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-loop", "1",  # Loop the image
            "-i", str(screenshot.image_path),  # Input image
            "-i", str(audio.audio_path),  # Input audio
            "-c:v", "libx264",  # H.264 video codec
            "-c:a", "aac",  # AAC audio codec
            "-b:a", "192k",  # Audio bitrate
            "-pix_fmt", "yuv420p",  # Pixel format for compatibility
            "-shortest",  # Stop when shortest input ends
            "-t", str(duration),  # Duration
        ]

        # Add video filter
        vf_filters = []

        # Scale to target resolution
        vf_filters.append(f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease")
        vf_filters.append(f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2")

        # Add Ken Burns effect (zoom and pan)
        if use_ken_burns:
            # Calculate zoom parameters
            zoom_start = 1.0
            zoom_end = 1.2
            total_frames = int(duration * self.fps)

            # Zoompan filter: subtle zoom in
            zoompan = (
                f"zoompan=z='min(zoom+0.0015,{zoom_end})'"
                f":d={total_frames}"
                f":x='iw/2-(iw/zoom/2)'"
                f":y='ih/2-(ih/zoom/2)'"
                f":fps={self.fps}"
                f":s={self.width}x{self.height}"
            )
            vf_filters.append(zoompan)
        else:
            # Set framerate without zoom
            vf_filters.append(f"fps={self.fps}")

        # Combine filters
        cmd.extend(["-vf", ",".join(vf_filters)])

        # Output
        cmd.append(str(output_path))

        # Run FFmpeg
        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def concatenate_clips(
        self,
        clip_paths: list[Path],
        output_path: Path,
        with_transitions: bool = True,
    ) -> Path:
        """Concatenate multiple video clips into one.

        Args:
            clip_paths: List of clip file paths
            output_path: Path to save concatenated video
            with_transitions: Apply crossfade transitions

        Returns:
            Path to concatenated video

        Raises:
            subprocess.CalledProcessError: If FFmpeg fails
        """
        if len(clip_paths) == 1:
            # Single clip, just copy
            import shutil
            shutil.copy(clip_paths[0], output_path)
            return output_path

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Add all input clips
        for clip_path in clip_paths:
            cmd.extend(["-i", str(clip_path)])

        if with_transitions and len(clip_paths) > 1:
            # Get clip durations
            durations = []
            for clip_path in clip_paths:
                duration = self._get_video_duration(clip_path)
                durations.append(duration)

            # Build complex filter with transitions
            num_inputs = len(clip_paths)
            filter_complex = self.transition_builder.build_complex_filter(
                num_inputs=num_inputs,
                scene_durations=durations,
                transition_duration=self.transition_duration,
                transition_type=self.transition_type,
            )

            # Add audio concatenation
            audio_concat = "".join(f"[{i}:a]" for i in range(num_inputs))
            audio_concat += f"concat=n={num_inputs}:v=0:a=1[outa]"

            full_filter = f"{filter_complex};{audio_concat}"

            cmd.extend([
                "-filter_complex", full_filter,
                "-map", "[outv]",
                "-map", "[outa]",
            ])
        else:
            # Simple concatenation without transitions
            concat_filter = f"concat=n={len(clip_paths)}:v=1:a=1[outv][outa]"
            cmd.extend([
                "-filter_complex", concat_filter,
                "-map", "[outv]",
                "-map", "[outa]",
            ])

        # Output encoding
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ])

        # Run FFmpeg
        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def burn_subtitles(
        self,
        video_path: Path,
        subtitle_path: Path,
        output_path: Path,
        font: str = "Arial",
        font_size: int = 24,
    ) -> Path:
        """Burn subtitles into video.

        Args:
            video_path: Input video file
            subtitle_path: SRT subtitle file
            output_path: Output video with subtitles
            font: Font name for subtitles
            font_size: Font size in points

        Returns:
            Path to video with burned subtitles

        Raises:
            subprocess.CalledProcessError: If FFmpeg fails
        """
        # Escape subtitle path for FFmpeg
        srt_path_escaped = str(subtitle_path).replace("\\", "\\\\").replace(":", "\\:")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vf", f"subtitles={srt_path_escaped}:force_style='FontName={font},FontSize={font_size}'",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",  # Copy audio without re-encoding
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def assemble_video(
        self,
        screenshots: list[Screenshot],
        audio_segments: list[AudioSegment],
        output_path: Path,
        subtitle_path: Path | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> Path:
        """Assemble complete video from all components.

        Args:
            screenshots: List of screenshots (one per scene)
            audio_segments: List of audio segments (one per scene)
            output_path: Final video output path
            subtitle_path: Optional SRT subtitle file
            progress_callback: Optional callback(message, progress)

        Returns:
            Path to final assembled video

        Raises:
            ValueError: If screenshots and audio don't match
            subprocess.CalledProcessError: If FFmpeg fails
        """
        if len(screenshots) != len(audio_segments):
            raise ValueError(
                f"Screenshot count ({len(screenshots)}) must match "
                f"audio count ({len(audio_segments)})"
            )

        # Create temporary directory for clips
        temp_dir = self.output_dir / "temp_clips"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Create individual scene clips
            clip_paths = []
            total_scenes = len(screenshots)

            for i, (screenshot, audio) in enumerate(zip(screenshots, audio_segments)):
                if progress_callback:
                    progress_callback(
                        f"Creating scene clip {i+1}/{total_scenes}",
                        i / (total_scenes + 2),  # +2 for concat and subtitle steps
                    )

                clip_path = temp_dir / f"clip_{i:03d}.mp4"
                self.create_scene_clip(screenshot, audio, clip_path)
                clip_paths.append(clip_path)

            # Step 2: Concatenate clips with transitions
            if progress_callback:
                progress_callback(
                    "Concatenating clips with transitions",
                    total_scenes / (total_scenes + 2),
                )

            if subtitle_path:
                # Create video without subtitles first
                temp_video = temp_dir / "video_no_subs.mp4"
                self.concatenate_clips(clip_paths, temp_video, with_transitions=True)

                # Step 3: Burn subtitles
                if progress_callback:
                    progress_callback(
                        "Burning subtitles",
                        (total_scenes + 1) / (total_scenes + 2),
                    )

                self.burn_subtitles(temp_video, subtitle_path, output_path)
            else:
                # No subtitles, output directly
                self.concatenate_clips(clip_paths, output_path, with_transitions=True)

            if progress_callback:
                progress_callback("Video assembly complete", 1.0)

            return output_path

        finally:
            # Cleanup temporary clips
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
