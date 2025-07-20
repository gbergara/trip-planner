"""
Internationalization service for the trip planner application.

This service handles language detection, translation loading,
and text translation functionality.
"""

import os
import gettext
from pathlib import Path
from typing import Optional

from ..core.config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, LOCALES_DIR

# Get the directory where the app is located
BASE_DIR = Path(__file__).parent.parent
LOCALES_PATH = BASE_DIR / "locales"

# Cache for loaded translations
_translations_cache = {}

def get_translation(language: str = DEFAULT_LANGUAGE) -> gettext.GNUTranslations:
    """Get translation object for the specified language."""
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    if language not in _translations_cache:
        try:
            translation = gettext.translation(
                'messages', 
                localedir=LOCALES_PATH, 
                languages=[language],
                fallback=True
            )
            _translations_cache[language] = translation
        except Exception:
            # Fallback to default language
            translation = gettext.translation(
                'messages', 
                localedir=LOCALES_PATH, 
                languages=[DEFAULT_LANGUAGE],
                fallback=True
            )
            _translations_cache[language] = translation
    
    return _translations_cache[language]

def translate(text: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Translate text to the specified language."""
    translation = get_translation(language)
    return translation.gettext(text)

# Alias for backward compatibility
_ = translate

def ngettext(singular: str, plural: str, count: int, language: str = DEFAULT_LANGUAGE) -> str:
    """Handle plural forms in translations."""
    translation = get_translation(language)
    return translation.ngettext(singular, plural, count)

def detect_language_from_request(accept_language: Optional[str]) -> str:
    """Detect preferred language from Accept-Language header."""
    if not accept_language:
        return DEFAULT_LANGUAGE
    
    # Parse Accept-Language header
    languages = []
    for lang_item in accept_language.split(','):
        lang_item = lang_item.strip()
        if ';' in lang_item:
            lang, priority = lang_item.split(';', 1)
            try:
                priority = float(priority.split('=')[1])
            except (ValueError, IndexError):
                priority = 1.0
        else:
            lang, priority = lang_item, 1.0
        
        lang = lang.strip().lower()[:2]  # Get just language code
        if lang in SUPPORTED_LANGUAGES:
            languages.append((lang, priority))
    
    if languages:
        # Sort by priority and return highest
        languages.sort(key=lambda x: x[1], reverse=True)
        return languages[0][0]
    
    return DEFAULT_LANGUAGE

def get_language_names() -> dict:
    """Get human-readable language names."""
    return {
        "en": "English",
        "es": "Español"
    }

def get_supported_languages() -> list:
    """Get list of supported language codes."""
    return SUPPORTED_LANGUAGES.copy() 