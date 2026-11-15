"""Shared list of supported languages and the fallback rule for translatable content.

Not literally "every language" - that's roughly 7,000 living languages, most with no realistic
professional-translation pipeline for a project like this. This is a genuinely broad, real-world set
covering every populated region, matching how large localized products actually scope language support.
Adding another language later is a data change, not a schema change: add its code here, add a row of
content per translatable item, add a frontend locale file.
"""

# code -> (English name, native name, is_rtl)
SUPPORTED_LANGUAGES: dict[str, tuple[str, str, bool]] = {
    "en": ("English", "English", False),
    "fr": ("French", "Français", False),
    "es": ("Spanish", "Español", False),
    "de": ("German", "Deutsch", False),
    "pt": ("Portuguese", "Português", False),
    "it": ("Italian", "Italiano", False),
    "nl": ("Dutch", "Nederlands", False),
    "pl": ("Polish", "Polski", False),
    "ru": ("Russian", "Русский", False),
    "tr": ("Turkish", "Türkçe", False),
    "ar": ("Arabic", "العربية", True),
    "zh": ("Chinese", "中文", False),
    "ja": ("Japanese", "日本語", False),
    "ko": ("Korean", "한국어", False),
    "hi": ("Hindi", "हिन्दी", False),
    "sw": ("Swahili", "Kiswahili", False),
}
DEFAULT_LANGUAGE = "en"
LANGUAGE_CODES = set(SUPPORTED_LANGUAGES)


def localized(field: dict | None, lang: str | None) -> str:
    """Reads one language out of a {code: text} field, falling back to English, then to any
    value present, then to an empty string. Never raises on missing/malformed data."""
    if not field:
        return ""
    if lang and lang in field and field[lang]:
        return field[lang]
    if field.get(DEFAULT_LANGUAGE):
        return field[DEFAULT_LANGUAGE]
    for v in field.values():
        if v:
            return v
    return ""


def normalize_translations(value: dict, *, required: tuple[str, ...] = (DEFAULT_LANGUAGE,)) -> dict:
    """Validates a {language_code: text} payload: unknown codes rejected, required languages present."""
    if not isinstance(value, dict) or not value:
        raise ValueError("Expected a non-empty object of {language_code: text}")
    cleaned = {}
    for code, text_ in value.items():
        if code not in LANGUAGE_CODES:
            raise ValueError(f"Unsupported language code: {code}")
        if not isinstance(text_, str) or not text_.strip():
            continue
        cleaned[code] = text_.strip()
    for req in required:
        if req not in cleaned:
            raise ValueError(f"Missing required language: {req}")
    return cleaned
