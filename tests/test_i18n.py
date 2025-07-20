import pytest
from unittest.mock import Mock, patch
from app.services.i18n_service import translate as _, detect_language_from_request, get_language_names, get_supported_languages

SUPPORTED_LANGUAGES = get_supported_languages()


@pytest.mark.unit
class TestI18nFunctions:
    """Test cases for internationalization functions."""
    
    def test_supported_languages(self):
        """Test that supported languages are correctly defined."""
        assert 'en' in SUPPORTED_LANGUAGES
        assert 'es' in SUPPORTED_LANGUAGES
        assert len(SUPPORTED_LANGUAGES) == 2
    
    def test_get_language_names(self):
        """Test getting language names."""
        names = get_language_names()
        
        assert 'en' in names
        assert 'es' in names
        assert names['en'] == 'English'
        assert names['es'] == 'Español'
    
    def test_translation_function_basic(self):
        """Test the basic translation function."""
        # Test with English (should return original)
        result = _("Hello", "en")
        assert result == "Hello"  # English is the default, no translation needed
        
        # Test with unsupported language (should fallback)
        result = _("Hello", "fr")
        assert result == "Hello"  # Should fallback to English
    
    def test_detect_language_from_accept_language(self):
        """Test language detection from Accept-Language header."""
        # Test Spanish preference
        result = detect_language_from_request("es-ES,es;q=0.9,en;q=0.8")
        assert result == "es"
        
        # Test English preference  
        result = detect_language_from_request("en-US,en;q=0.9")
        assert result == "en"
    
    def test_detect_language_unsupported_language(self):
        """Test language detection with unsupported language."""
        # Test with unsupported languages
        result = detect_language_from_request("fr-FR,de;q=0.9")
        assert result == "en"  # Should default to English
    
    def test_detect_language_no_headers(self):
        """Test language detection when no language info is available."""
        result = detect_language_from_request(None)
        assert result == "en"  # Should default to English
        
        result = detect_language_from_request("")
        assert result == "en"  # Should default to English
    
    def test_detect_language_complex_accept_language(self):
        """Test language detection with complex Accept-Language header."""
        # Should find English (supported language with highest priority)
        result = detect_language_from_request("fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5")
        assert result == "en"
    
    def test_detect_language_case_handling(self):
        """Test that language detection handles cases correctly."""
        # Test various case combinations
        result = detect_language_from_request("ES-es,EN;q=0.9")
        assert result == "es"  # Should find Spanish first
        
        result = detect_language_from_request("EN-us,ES;q=0.8")
        assert result == "en"  # Should find English first
    
    def test_detect_language_priority_handling(self):
        """Test that language detection respects priority values."""
        # Spanish has higher priority
        result = detect_language_from_request("en;q=0.7,es;q=0.9")
        assert result == "es"
        
        # English has higher priority
        result = detect_language_from_request("es;q=0.7,en;q=0.9")
        assert result == "en"


@pytest.mark.integration
class TestI18nIntegration:
    """Integration tests for i18n functionality."""
    
    def test_translation_files_exist(self):
        """Test that translation files exist for supported languages."""
        import os
        
        for lang in SUPPORTED_LANGUAGES:
            if lang != 'en':  # English doesn't need translation files
                po_file = f"app/locales/{lang}/LC_MESSAGES/messages.po"
                mo_file = f"app/locales/{lang}/LC_MESSAGES/messages.mo"
                
                assert os.path.exists(po_file), f"Missing .po file for {lang}"
                assert os.path.exists(mo_file), f"Missing .mo file for {lang}"
    
    def test_key_translations_present(self):
        """Test that key translation strings are present in translation files."""
        import os
        
        # Key strings that should be translated
        key_strings = [
            "My Trips",
            "All Bookings", 
            "Create Trip",
            "Add Booking",
            "Confirmed",
            "Pending",
            "Cancelled"
        ]
        
        # Check Spanish translation file
        es_po_file = "app/locales/es/LC_MESSAGES/messages.po"
        if os.path.exists(es_po_file):
            with open(es_po_file, 'r', encoding='utf-8') as f:
                po_content = f.read()
                
                for key_string in key_strings:
                    assert f'msgid "{key_string}"' in po_content, f"Missing translation for: {key_string}"
    
    def test_translation_fallback(self):
        """Test that translation fallback works correctly."""
        # Test with supported language
        result = _("Hello", "en")
        assert isinstance(result, str)
        
        # Test with unsupported language (should fallback)
        result = _("Hello", "fr")
        assert isinstance(result, str)
    
    def test_translation_cache_functionality(self):
        """Test that translation caching works."""
        from app.services.i18n_service import get_translation
        
        # Get translation twice - should use cache the second time
        trans1 = get_translation("es")
        trans2 = get_translation("es")
        
        # Should be the same object (cached)
        assert trans1 is trans2


@pytest.mark.slow
class TestTranslationFileIntegrity:
    """Slow tests for translation file integrity."""
    
    def test_mo_files_are_compiled(self):
        """Test that .mo files are properly compiled from .po files (allowing small mtime difference)."""
        import os
        
        for lang in SUPPORTED_LANGUAGES:
            if lang != 'en':
                po_file = f"app/locales/{lang}/LC_MESSAGES/messages.po"
                mo_file = f"app/locales/{lang}/LC_MESSAGES/messages.mo"
                
                if os.path.exists(po_file):
                    po_mtime = os.path.getmtime(po_file)
                    if os.path.exists(mo_file):
                        mo_mtime = os.path.getmtime(mo_file)
                        # Allow up to 2 seconds difference due to filesystem/tool quirks
                        assert mo_mtime + 2 >= po_mtime, f".mo file for {lang} is older than .po file (mo: {mo_mtime}, po: {po_mtime})"
    
    def test_translation_coverage(self):
        """Test translation coverage for different languages."""
        import os
        import re
        
        # Extract msgid strings from English (base) templates
        template_strings = set()
        
        # Scan template files for translatable strings
        template_dirs = ["app/templates"]
        for template_dir in template_dirs:
            if os.path.exists(template_dir):
                for root, dirs, files in os.walk(template_dir):
                    for file in files:
                        if file.endswith('.html'):
                            filepath = os.path.join(root, file)
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                # Find translation function calls
                                patterns = [
                                    r'_\("([^"]+)"\)',
                                    r"_\('([^']+)'\)",
                                    r'{%\s*if\s+_\s*%}{{\s*_\("([^"]+)"\)\s*}}{%\s*else\s*%}([^{%]+){%\s*endif\s*%}'
                                ]
                                
                                for pattern in patterns:
                                    matches = re.findall(pattern, content)
                                    for match in matches:
                                        if isinstance(match, tuple):
                                            template_strings.add(match[0])
                                        else:
                                            template_strings.add(match)
        
        # Check Spanish translation coverage
        es_po_file = "app/locales/es/LC_MESSAGES/messages.po"
        if os.path.exists(es_po_file) and template_strings:
            with open(es_po_file, 'r', encoding='utf-8') as f:
                po_content = f.read()
                
                translated_strings = set(re.findall(r'msgid "([^"]+)"', po_content))
                
                # Calculate coverage
                coverage = len(template_strings & translated_strings) / len(template_strings) if template_strings else 1
                
                # Should have reasonable translation coverage (at least 50% for now)
                assert coverage >= 0.5, f"Spanish translation coverage is only {coverage:.2%}" 