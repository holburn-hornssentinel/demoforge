"""SRT subtitle generation from script and audio timings."""

from pathlib import Path

import pysrt

from demoforge.models import AudioSegment, DemoScript, SubtitleEntry


class SubtitleGenerator:
    """Generates SRT subtitle files from demo scripts and audio segments."""

    def __init__(
        self,
        output_dir: Path = Path("/app/output/subtitles"),
        max_chars_per_line: int = 42,
        max_lines: int = 2,
    ) -> None:
        """Initialize subtitle generator.

        Args:
            output_dir: Directory to save SRT files
            max_chars_per_line: Maximum characters per subtitle line
            max_lines: Maximum number of lines per subtitle
        """
        self.output_dir = output_dir
        self.max_chars_per_line = max_chars_per_line
        self.max_lines = max_lines
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_from_audio(
        self,
        audio_segments: list[AudioSegment],
        project_id: str,
    ) -> tuple[list[SubtitleEntry], Path]:
        """Generate subtitles from audio segments with precise timings.

        Args:
            audio_segments: List of audio segments with start times and durations
            project_id: Project identifier for filename

        Returns:
            Tuple of (SubtitleEntry list, Path to SRT file)
        """
        subtitle_entries = []
        index = 1

        for segment in audio_segments:
            # Split text into subtitle-sized chunks
            chunks = self._split_text(segment.text)

            # Calculate timing for each chunk
            total_duration = segment.duration_seconds
            chunk_duration = total_duration / len(chunks)

            for i, chunk_text in enumerate(chunks):
                start_time = segment.start_time + (i * chunk_duration)
                end_time = start_time + chunk_duration

                entry = SubtitleEntry(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=chunk_text,
                )
                subtitle_entries.append(entry)
                index += 1

        # Save to SRT file
        srt_path = self.output_dir / f"{project_id}.srt"
        self.save_srt(subtitle_entries, srt_path)

        return subtitle_entries, srt_path

    def generate_from_script(
        self,
        script: DemoScript,
        project_id: str,
    ) -> tuple[list[SubtitleEntry], Path]:
        """Generate subtitles from script with estimated timings.

        Use this when audio segments are not yet available.
        Timings are estimated based on word count (150 words/min).

        Args:
            script: Demo script with scenes
            project_id: Project identifier

        Returns:
            Tuple of (SubtitleEntry list, Path to SRT file)
        """
        subtitle_entries = []
        index = 1
        current_time = 0.0

        # Process intro
        if script.intro:
            intro_duration = self._estimate_duration(script.intro)
            chunks = self._split_text(script.intro)
            chunk_duration = intro_duration / len(chunks)

            for chunk_text in chunks:
                entry = SubtitleEntry(
                    index=index,
                    start_time=current_time,
                    end_time=current_time + chunk_duration,
                    text=chunk_text,
                )
                subtitle_entries.append(entry)
                index += 1
                current_time += chunk_duration

        # Process scenes
        for scene in script.scenes:
            if not scene.narration:
                continue

            chunks = self._split_text(scene.narration)
            chunk_duration = scene.duration_seconds / len(chunks)

            for chunk_text in chunks:
                entry = SubtitleEntry(
                    index=index,
                    start_time=current_time,
                    end_time=current_time + chunk_duration,
                    text=chunk_text,
                )
                subtitle_entries.append(entry)
                index += 1
                current_time += chunk_duration

        # Process outro
        if script.outro:
            outro_duration = self._estimate_duration(script.outro)
            chunks = self._split_text(script.outro)
            chunk_duration = outro_duration / len(chunks)

            for chunk_text in chunks:
                entry = SubtitleEntry(
                    index=index,
                    start_time=current_time,
                    end_time=current_time + chunk_duration,
                    text=chunk_text,
                )
                subtitle_entries.append(entry)
                index += 1
                current_time += chunk_duration

        # Save to SRT file
        srt_path = self.output_dir / f"{project_id}.srt"
        self.save_srt(subtitle_entries, srt_path)

        return subtitle_entries, srt_path

    def _split_text(self, text: str) -> list[str]:
        """Split text into subtitle-sized chunks.

        Attempts to break at sentence boundaries for natural reading.

        Args:
            text: Text to split

        Returns:
            List of subtitle chunks
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Split into sentences (rough approximation)
        import re

        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # Check if adding this sentence exceeds limits
            test_chunk = (
                current_chunk + " " + sentence if current_chunk else sentence
            ).strip()

            if self._fits_subtitle(test_chunk):
                current_chunk = test_chunk
            else:
                # Current chunk is full, start new one
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # Single sentence too long, force split by words
                    word_chunks = self._split_long_sentence(sentence)
                    chunks.extend(word_chunks)
                    current_chunk = ""

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks or [text]  # Fallback to original if splitting fails

    def _fits_subtitle(self, text: str) -> bool:
        """Check if text fits subtitle constraints.

        Args:
            text: Text to check

        Returns:
            True if text fits within max_chars_per_line and max_lines
        """
        lines = self._wrap_text(text)
        if len(lines) > self.max_lines:
            return False

        return all(len(line) <= self.max_chars_per_line for line in lines)

    def _wrap_text(self, text: str) -> list[str]:
        """Wrap text to multiple lines.

        Args:
            text: Text to wrap

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if len(test_line) <= self.max_chars_per_line:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _split_long_sentence(self, sentence: str) -> list[str]:
        """Force split a long sentence into chunks.

        Args:
            sentence: Long sentence to split

        Returns:
            List of chunks
        """
        words = sentence.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            test_length = current_length + len(word) + 1  # +1 for space
            if test_length <= self.max_chars_per_line:
                current_chunk.append(word)
                current_length = test_length
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _estimate_duration(self, text: str) -> float:
        """Estimate duration for text based on word count.

        Args:
            text: Text to estimate

        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        # Average speaking rate: 150 words/min = 2.5 words/sec
        return word_count / 2.5

    def save_srt(self, entries: list[SubtitleEntry], output_path: Path) -> None:
        """Save subtitle entries to SRT file.

        Args:
            entries: List of subtitle entries
            output_path: Path to save SRT file
        """
        srt_file = pysrt.SubRipFile()

        for entry in entries:
            # Convert seconds to pysrt time format
            start_ms = int(entry.start_time * 1000)
            end_ms = int(entry.end_time * 1000)

            srt_item = pysrt.SubRipItem(
                index=entry.index,
                start=self._ms_to_srt_time(start_ms),
                end=self._ms_to_srt_time(end_ms),
                text=entry.text,
            )
            srt_file.append(srt_item)

        # Save to file
        srt_file.save(str(output_path), encoding="utf-8")

    def _ms_to_srt_time(self, milliseconds: int) -> pysrt.SubRipTime:
        """Convert milliseconds to SubRipTime.

        Args:
            milliseconds: Time in milliseconds

        Returns:
            SubRipTime object
        """
        hours = milliseconds // 3600000
        milliseconds %= 3600000
        minutes = milliseconds // 60000
        milliseconds %= 60000
        seconds = milliseconds // 1000
        milliseconds %= 1000

        return pysrt.SubRipTime(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds,
        )

    def load_srt(self, srt_path: Path) -> list[SubtitleEntry]:
        """Load SRT file into SubtitleEntry list.

        Args:
            srt_path: Path to SRT file

        Returns:
            List of SubtitleEntry objects
        """
        srt_file = pysrt.open(str(srt_path))
        entries = []

        for item in srt_file:
            start_seconds = (
                item.start.hours * 3600
                + item.start.minutes * 60
                + item.start.seconds
                + item.start.milliseconds / 1000.0
            )
            end_seconds = (
                item.end.hours * 3600
                + item.end.minutes * 60
                + item.end.seconds
                + item.end.milliseconds / 1000.0
            )

            entry = SubtitleEntry(
                index=item.index,
                start_time=start_seconds,
                end_time=end_seconds,
                text=item.text,
            )
            entries.append(entry)

        return entries
