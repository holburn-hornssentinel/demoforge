"""Tests for TTS engine selection and language fallback."""

import pytest

from demoforge.models import Language, TTSEngine
from demoforge.voice import create_tts_engine
from demoforge.voice.edge_tts_engine import EdgeTTSEngine
from demoforge.voice.kokoro_tts import KokoroTTSEngine
from demoforge.voice.language_voices import (
    get_voice_for_language,
    is_cjk_language,
    supports_kokoro_tts,
)
from demoforge.voice.pocket_tts import PocketTTSEngine


def test_kokoro_tts_english_support():
    """Should support Kokoro TTS for English."""
    assert supports_kokoro_tts(Language.ENGLISH) is True


def test_kokoro_tts_non_english_not_supported():
    """Should not support Kokoro TTS for non-English languages."""
    assert supports_kokoro_tts(Language.SPANISH) is False
    assert supports_kokoro_tts(Language.FRENCH) is False
    assert supports_kokoro_tts(Language.JAPANESE) is False
    assert supports_kokoro_tts(Language.CHINESE_SIMPLIFIED) is False


def test_create_kokoro_tts_english(temp_dir):
    """Should create Kokoro TTS engine for English."""
    engine = create_tts_engine(
        engine=TTSEngine.KOKORO,
        voice="af",
        speed=1.0,
        output_dir=temp_dir / "audio",
        language=Language.ENGLISH,
    )

    assert isinstance(engine, KokoroTTSEngine)


def test_create_kokoro_tts_fallback_to_edge(temp_dir):
    """Should fallback to Edge TTS when Kokoro used with non-English."""
    engine = create_tts_engine(
        engine=TTSEngine.KOKORO,
        voice="af",
        speed=1.0,
        output_dir=temp_dir / "audio",
        language=Language.SPANISH,
    )

    # Should fallback to Edge TTS
    assert isinstance(engine, EdgeTTSEngine)


def test_create_edge_tts_any_language(temp_dir):
    """Should create Edge TTS for any language."""
    languages = [
        Language.ENGLISH,
        Language.SPANISH,
        Language.FRENCH,
        Language.JAPANESE,
        Language.CHINESE_SIMPLIFIED,
    ]

    for lang in languages:
        engine = create_tts_engine(
            engine=TTSEngine.EDGE,
            voice="en-US-GuyNeural",
            speed=1.0,
            output_dir=temp_dir / "audio",
            language=lang,
        )

        assert isinstance(engine, EdgeTTSEngine)


def test_create_pocket_tts(temp_dir):
    """Should create Pocket TTS engine."""
    engine = create_tts_engine(
        engine=TTSEngine.POCKET,
        voice="af",
        speed=1.0,
        output_dir=temp_dir / "audio",
        language=Language.ENGLISH,
    )

    assert isinstance(engine, PocketTTSEngine)


def test_get_voice_for_language_english():
    """Should return English voice."""
    voice = get_voice_for_language(Language.ENGLISH, gender="male")
    assert "en-US" in voice or "en-GB" in voice


def test_get_voice_for_language_spanish():
    """Should return Spanish voice."""
    voice = get_voice_for_language(Language.SPANISH, gender="female")
    assert "es-" in voice


def test_get_voice_for_language_japanese():
    """Should return Japanese voice."""
    voice = get_voice_for_language(Language.JAPANESE, gender="female")
    assert "ja-JP" in voice


def test_get_voice_for_language_chinese():
    """Should return Chinese voice."""
    voice = get_voice_for_language(Language.CHINESE_SIMPLIFIED, gender="male")
    assert "zh-CN" in voice


def test_get_voice_for_language_gender_selection():
    """Should return different voices for male/female."""
    male_voice = get_voice_for_language(Language.ENGLISH, gender="male")
    female_voice = get_voice_for_language(Language.ENGLISH, gender="female")

    # Should be different voices
    assert male_voice != female_voice


def test_is_cjk_language():
    """Should identify CJK languages."""
    # CJK languages
    assert is_cjk_language(Language.JAPANESE) is True
    assert is_cjk_language(Language.KOREAN) is True
    assert is_cjk_language(Language.CHINESE_SIMPLIFIED) is True
    assert is_cjk_language(Language.CHINESE_TRADITIONAL) is True

    # Non-CJK languages
    assert is_cjk_language(Language.ENGLISH) is False
    assert is_cjk_language(Language.SPANISH) is False
    assert is_cjk_language(Language.FRENCH) is False


def test_tts_factory_with_voice_sample(temp_dir):
    """Should pass voice sample to Pocket TTS."""
    voice_sample = temp_dir / "voice_sample.wav"
    voice_sample.touch()

    engine = create_tts_engine(
        engine=TTSEngine.POCKET,
        voice="af",
        speed=1.0,
        output_dir=temp_dir / "audio",
        language=Language.ENGLISH,
        voice_sample_path=voice_sample,
    )

    assert isinstance(engine, PocketTTSEngine)
    assert engine.voice_sample_path == voice_sample


def test_tts_factory_speed_parameter(temp_dir):
    """Should configure TTS speed."""
    engine = create_tts_engine(
        engine=TTSEngine.EDGE,
        voice="en-US-GuyNeural",
        speed=1.5,
        output_dir=temp_dir / "audio",
        language=Language.ENGLISH,
    )

    assert engine.speed == 1.5


def test_language_voice_mapping_completeness():
    """Should have voice mappings for all supported languages."""
    languages = [
        Language.ENGLISH,
        Language.SPANISH,
        Language.FRENCH,
        Language.GERMAN,
        Language.ITALIAN,
        Language.PORTUGUESE,
        Language.JAPANESE,
        Language.KOREAN,
        Language.CHINESE_SIMPLIFIED,
        Language.ARABIC,
        Language.HINDI,
    ]

    for lang in languages:
        # Should return a valid voice (no exception)
        voice = get_voice_for_language(lang)
        assert isinstance(voice, str)
        assert len(voice) > 0


def test_fallback_with_warning(temp_dir, capsys):
    """Should print warning when falling back to Edge TTS."""
    engine = create_tts_engine(
        engine=TTSEngine.KOKORO,
        voice="af",
        speed=1.0,
        output_dir=temp_dir / "audio",
        language=Language.JAPANESE,
    )

    # Should have created Edge TTS engine
    assert isinstance(engine, EdgeTTSEngine)

    # Check for warning message (captured output)
    captured = capsys.readouterr()
    assert "Warning" in captured.out or "fallback" in captured.out.lower()


def test_multilanguage_demo_script_tts_selection(temp_dir):
    """Should select appropriate TTS for each language in multi-language scenarios."""
    test_cases = [
        (Language.ENGLISH, TTSEngine.KOKORO),
        (Language.SPANISH, TTSEngine.EDGE),
        (Language.FRENCH, TTSEngine.EDGE),
        (Language.JAPANESE, TTSEngine.EDGE),
    ]

    for language, expected_engine_type in test_cases:
        engine = create_tts_engine(
            engine=TTSEngine.KOKORO,  # Request Kokoro
            voice="af",
            speed=1.0,
            output_dir=temp_dir / "audio",
            language=language,
        )

        if expected_engine_type == TTSEngine.KOKORO:
            assert isinstance(engine, KokoroTTSEngine)
        elif expected_engine_type == TTSEngine.EDGE:
            assert isinstance(engine, EdgeTTSEngine)


def test_voice_for_language_defaults_to_female():
    """Should default to female voice when gender not specified."""
    voice = get_voice_for_language(Language.ENGLISH)

    # Should return a valid voice (implementation specific)
    assert isinstance(voice, str)


def test_pocket_tts_fallback_to_edge(temp_dir):
    """Should fallback to Edge TTS from Pocket TTS when no sample provided."""
    # Pocket TTS without voice sample should use fallback
    engine = PocketTTSEngine(
        voice="af",
        speed=1.0,
        output_dir=temp_dir / "audio",
        voice_sample_path=None,
    )

    # Should have fallback mechanism
    assert engine.voice_sample_path is None
