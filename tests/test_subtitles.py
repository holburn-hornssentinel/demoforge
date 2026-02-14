"""Tests for subtitle generation."""

import pytest

from demoforge.assembler.subtitles import SubtitleGenerator
from demoforge.models import AudioSegment, SubtitleEntry


def test_subtitle_generator_initialization(temp_dir):
    """Should initialize with output directory."""
    generator = SubtitleGenerator(
        output_dir=temp_dir / "subtitles",
        max_chars_per_line=42,
        max_lines=2,
    )

    assert generator.output_dir == temp_dir / "subtitles"
    assert generator.max_chars_per_line == 42
    assert generator.max_lines == 2
    assert generator.output_dir.exists()


def test_split_text_short():
    """Should not split short text."""
    generator = SubtitleGenerator(max_chars_per_line=42)

    text = "This is a short sentence."
    chunks = generator._split_text(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_text_long():
    """Should split long text at word boundaries."""
    generator = SubtitleGenerator(max_chars_per_line=30)

    text = "This is a very long sentence that needs to be split into multiple subtitle chunks for readability."
    chunks = generator._split_text(text)

    # Should split into multiple chunks
    assert len(chunks) > 1

    # Each chunk should be within limit
    for chunk in chunks:
        assert len(chunk) <= generator.max_chars_per_line


def test_split_text_preserves_words():
    """Should not split words in the middle."""
    generator = SubtitleGenerator(max_chars_per_line=20)

    text = "Supercalifragilisticexpialidocious is a long word"
    chunks = generator._split_text(text)

    # Long words should remain intact
    assert "Supercalifragilisticexpialidocious" in chunks[0]


def test_generate_from_audio(temp_dir):
    """Should generate subtitles from audio segments."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    audio_segments = [
        AudioSegment(
            scene_id="scene_001",
            text="Welcome to DemoForge.",
            start_time=0.0,
            duration_seconds=3.0,
            audio_path=temp_dir / "audio1.wav",
        ),
        AudioSegment(
            scene_id="scene_002",
            text="This is an automated demo video generator.",
            start_time=3.0,
            duration_seconds=4.0,
            audio_path=temp_dir / "audio2.wav",
        ),
    ]

    subtitles, srt_path = generator.generate_from_audio(
        audio_segments=audio_segments,
        project_id="test_project",
    )

    assert len(subtitles) >= 2
    assert srt_path.exists()
    assert srt_path.name == "test_project.srt"

    # Check subtitle timings
    first_subtitle = subtitles[0]
    assert first_subtitle.start_time == 0.0
    assert first_subtitle.end_time <= 3.0


def test_generate_from_script(temp_dir, sample_script):
    """Should generate subtitles from demo script."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    subtitles, srt_path = generator.generate_from_script(
        script=sample_script,
        project_id="test_project",
    )

    assert len(subtitles) > 0
    assert srt_path.exists()

    # Check that subtitles cover all scenes
    total_scenes = len(sample_script.scenes)
    assert len(subtitles) >= total_scenes


def test_save_srt_format(temp_dir):
    """Should save subtitles in SRT format."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    subtitles = [
        SubtitleEntry(
            index=1,
            start_time=0.0,
            end_time=3.0,
            text="Welcome to the demo.",
        ),
        SubtitleEntry(
            index=2,
            start_time=3.0,
            end_time=6.0,
            text="This is scene two.",
        ),
    ]

    srt_path = temp_dir / "subtitles" / "test.srt"
    generator.save_srt(subtitles, srt_path)

    assert srt_path.exists()

    # Read and verify SRT format
    content = srt_path.read_text()
    assert "1" in content  # First subtitle index
    assert "00:00:00,000 --> 00:00:03,000" in content
    assert "Welcome to the demo." in content


def test_subtitle_timing_calculation(temp_dir):
    """Should calculate correct subtitle timings."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    audio_segments = [
        AudioSegment(
            scene_id="scene_001",
            text="First segment that is moderately long to test splitting",
            start_time=0.0,
            duration_seconds=6.0,
            audio_path=temp_dir / "audio.wav",
        ),
    ]

    subtitles, _ = generator.generate_from_audio(audio_segments, "test")

    # Check timing continuity
    for i in range(len(subtitles) - 1):
        current = subtitles[i]
        next_sub = subtitles[i + 1]

        # End time should match next start time (or be close)
        assert current.end_time <= next_sub.start_time + 0.1


def test_subtitle_text_cleanup(temp_dir):
    """Should clean up subtitle text formatting."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    audio_segments = [
        AudioSegment(
            scene_id="scene_001",
            text="  Text with   extra   spaces  ",
            start_time=0.0,
            duration_seconds=3.0,
            audio_path=temp_dir / "audio.wav",
        ),
    ]

    subtitles, _ = generator.generate_from_audio(audio_segments, "test")

    # Text should be cleaned
    for subtitle in subtitles:
        # No leading/trailing spaces
        assert subtitle.text == subtitle.text.strip()
        # No multiple consecutive spaces
        assert "   " not in subtitle.text


def test_cjk_character_counting():
    """Should count CJK characters correctly for subtitle length."""
    generator = SubtitleGenerator(max_chars_per_line=20)

    # CJK text (Chinese)
    cjk_text = "这是一个很长的中文句子需要被分割"
    chunks = generator._split_text(cjk_text)

    # Should handle CJK properly
    assert len(chunks) >= 1


def test_empty_audio_segments(temp_dir):
    """Should handle empty audio segments gracefully."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    subtitles, srt_path = generator.generate_from_audio(
        audio_segments=[],
        project_id="empty_test",
    )

    assert len(subtitles) == 0
    assert srt_path.exists()


def test_subtitle_index_sequential(temp_dir):
    """Should assign sequential indices to subtitles."""
    generator = SubtitleGenerator(output_dir=temp_dir / "subtitles")

    audio_segments = [
        AudioSegment(
            scene_id=f"scene_{i}",
            text=f"Segment {i}",
            start_time=i * 3.0,
            duration_seconds=3.0,
            audio_path=temp_dir / f"audio_{i}.wav",
        )
        for i in range(5)
    ]

    subtitles, _ = generator.generate_from_audio(audio_segments, "test")

    # Indices should be sequential starting from 1
    for i, subtitle in enumerate(subtitles, start=1):
        assert subtitle.index == i
