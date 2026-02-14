"""Language-to-voice mappings for multi-language TTS support."""

from demoforge.models import Language

# Edge TTS voice mappings for different languages
# Format: Language -> (male_voice, female_voice)
EDGE_TTS_VOICES = {
    Language.ENGLISH: ("en-US-GuyNeural", "en-US-AriaNeural"),
    Language.SPANISH: ("es-ES-AlvaroNeural", "es-ES-ElviraNeural"),
    Language.FRENCH: ("fr-FR-HenriNeural", "fr-FR-DeniseNeural"),
    Language.GERMAN: ("de-DE-ConradNeural", "de-DE-KatjaNeural"),
    Language.ITALIAN: ("it-IT-DiegoNeural", "it-IT-ElsaNeural"),
    Language.PORTUGUESE: ("pt-BR-AntonioNeural", "pt-BR-FranciscaNeural"),
    Language.RUSSIAN: ("ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"),
    Language.JAPANESE: ("ja-JP-KeitaNeural", "ja-JP-NanamiNeural"),
    Language.KOREAN: ("ko-KR-InJoonNeural", "ko-KR-SunHiNeural"),
    Language.CHINESE_SIMPLIFIED: ("zh-CN-YunxiNeural", "zh-CN-XiaoxiaoNeural"),
    Language.CHINESE_TRADITIONAL: ("zh-TW-YunJheNeural", "zh-TW-HsiaoChenNeural"),
    Language.ARABIC: ("ar-SA-HamedNeural", "ar-SA-ZariyahNeural"),
    Language.HINDI: ("hi-IN-MadhurNeural", "hi-IN-SwaraNeural"),
    Language.DUTCH: ("nl-NL-MaartenNeural", "nl-NL-ColetteNeural"),
    Language.POLISH: ("pl-PL-MarekNeural", "pl-PL-ZofiaNeural"),
    Language.TURKISH: ("tr-TR-AhmetNeural", "tr-TR-EmelNeural"),
    Language.SWEDISH: ("sv-SE-MattiasNeural", "sv-SE-SofieNeural"),
    Language.DANISH: ("da-DK-JeppeNeural", "da-DK-ChristelNeural"),
    Language.NORWEGIAN: ("nb-NO-FinnNeural", "nb-NO-PernilleNeural"),
    Language.FINNISH: ("fi-FI-HarriNeural", "fi-FI-NooraNeural"),
}


def get_voice_for_language(
    language: Language, gender: str = "female"
) -> str:
    """Get appropriate TTS voice for a language.

    Args:
        language: Target language
        gender: Preferred gender ("male" or "female")

    Returns:
        Voice ID for Edge TTS

    Examples:
        >>> get_voice_for_language(Language.SPANISH, "female")
        'es-ES-ElviraNeural'
        >>> get_voice_for_language(Language.JAPANESE, "male")
        'ja-JP-KeitaNeural'
    """
    if language not in EDGE_TTS_VOICES:
        # Fallback to English
        language = Language.ENGLISH

    male_voice, female_voice = EDGE_TTS_VOICES[language]

    if gender.lower() == "male":
        return male_voice
    else:
        return female_voice


def is_cjk_language(language: Language) -> bool:
    """Check if language uses CJK (Chinese, Japanese, Korean) characters.

    Args:
        language: Language to check

    Returns:
        True if CJK language
    """
    return language in [
        Language.JAPANESE,
        Language.KOREAN,
        Language.CHINESE_SIMPLIFIED,
        Language.CHINESE_TRADITIONAL,
    ]


def supports_kokoro_tts(language: Language) -> bool:
    """Check if Kokoro TTS supports this language.

    Kokoro TTS currently only supports English.

    Args:
        language: Language to check

    Returns:
        True if Kokoro supports this language
    """
    return language == Language.ENGLISH
