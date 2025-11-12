"""Translation component for Nepali-English translation and transliteration.

This module provides translation utilities for converting text between Nepali
(Devanagari script) and English, including:
- Nepali to English translation
- English to Nepali translation
- Transliteration handling (Devanagari ↔ Roman)
- Automatic language detection

Architecture:
    - LanguageDetector: Fast script detection using Unicode ranges
    - Translator: LLM-powered translation and transliteration service
    - BaseLLMProvider: Handles all LLM operations with automatic caching

Performance Optimizations:
    - Automatic caching at the LLM provider level
    - Fast character-range based language detection (no LLM call)
    - Efficient Unicode range checks for Devanagari script detection

LLM Integration:
    - All translation and transliteration done via LLM generate_text()
    - Context-aware, high-quality results
    - Proper handling of Nepali names, titles, and cultural context
    - Support for mixed-script text (common in Nepal)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from nes.core.utils.devanagari import contains_devanagari

# Configure logging
logger = logging.getLogger(__name__)


class LanguageDetector:
    """Language detector for identifying Nepali and English text.

    Uses character range analysis to detect Devanagari script (Nepali)
    versus Latin script (English).
    """

    def detect(self, text: str) -> str:
        """Detect the language of the given text.

        Analyzes character ranges to determine if text is primarily
        Nepali (Devanagari) or English (Latin).

        Args:
            text: The text to analyze

        Returns:
            Language code: "ne" for Nepali, "en" for English

        Examples:
            >>> detector = LanguageDetector()
            >>> detector.detect("राम चन्द्र पौडेल")
            'ne'
            >>> detector.detect("Ram Chandra Poudel")
            'en'
        """
        if not text or not text.strip():
            return "en"  # Default to English for empty text

        # Count Devanagari characters
        devanagari_count = sum(1 for c in text if contains_devanagari(c))

        # Count Latin characters (basic ASCII letters)
        latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 128)

        # Determine language based on character counts
        if devanagari_count > latin_count:
            return "ne"
        else:
            return "en"

    def is_devanagari(self, text: str) -> bool:
        """Check if text contains Devanagari characters.

        Args:
            text: The text to check

        Returns:
            True if text contains any Devanagari characters
        """
        return contains_devanagari(text)

    def is_latin(self, text: str) -> bool:
        """Check if text contains Latin characters.

        Args:
            text: The text to check

        Returns:
            True if text contains any Latin characters
        """
        return any(c.isalpha() and ord(c) < 128 for c in text)


class Translator:
    """Translator for converting text between Nepali and English.

    Provides translation capabilities using LLM providers.
    Supports both translation and transliteration.

    Attributes:
        llm_provider: The LLM provider instance to use for translation
        language_detector: Language detector instance
    """

    def __init__(
        self,
        llm_provider: "BaseLLMProvider",
    ):
        """Initialize the translator.

        Args:
            llm_provider: The LLM provider instance to use (required)
        """
        from .providers.base import BaseLLMProvider

        if not isinstance(llm_provider, BaseLLMProvider):
            raise TypeError(
                f"llm_provider must be an instance of BaseLLMProvider, "
                f"got {type(llm_provider).__name__}"
            )

        self.llm_provider = llm_provider
        self.language_detector = LanguageDetector()

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translate text between Nepali and English.

        Translates text from source language to target language. If source
        language is not specified, it will be automatically detected.

        Args:
            text: The text to translate
            target_lang: Target language code ("en" or "ne")
            source_lang: Source language code (optional, auto-detected if not provided)

        Returns:
            Dictionary containing:
                - translated_text: The translated text
                - detected_language: The detected source language (if auto-detected)
                - source_language: The source language used
                - target_language: The target language
                - transliteration: Transliterated version (if applicable)

        Examples:
            >>> translator = Translator()
            >>> result = await translator.translate(
            ...     text="राम चन्द्र पौडेल",
            ...     source_lang="ne",
            ...     target_lang="en"
            ... )
            >>> print(result["translated_text"])
            'Ram Chandra Poudel'
        """
        # Auto-detect source language if not provided
        detected_lang = source_lang
        if not source_lang:
            detected_lang = self.language_detector.detect(text)

        # Perform translation
        if detected_lang == target_lang:
            # Same language, no translation needed
            translated = text
        else:
            # Use LLM provider's generate_text for translation (caching handled at provider level)
            translated = await self._translate_text(
                text=text, source_lang=detected_lang, target_lang=target_lang
            )

        # Build result
        result = {
            "translated_text": translated,
            "source_language": detected_lang,
            "target_language": target_lang,
        }

        # Add detected language if it was auto-detected
        if not source_lang:
            result["detected_language"] = detected_lang

        # Add transliteration if applicable (using LLM)
        if detected_lang == "ne" and target_lang == "en":
            result["transliteration"] = await self.transliterate_text(
                text, direction="to_roman"
            )
        elif detected_lang == "en" and target_lang == "ne":
            result["transliteration"] = await self.transliterate_text(
                text, direction="to_devanagari"
            )

        return result

    async def transliterate_text(
        self,
        text: str,
        direction: str = "auto",
    ) -> str:
        """Transliterate text between Devanagari and Roman scripts using LLM.

        Args:
            text: The text to transliterate
            direction: Transliteration direction:
                - "auto": Auto-detect based on script
                - "to_roman": Devanagari to Roman
                - "to_devanagari": Roman to Devanagari

        Returns:
            Transliterated text
        """
        if direction == "auto":
            # Auto-detect direction
            if contains_devanagari(text):
                direction = "to_roman"
            else:
                direction = "to_devanagari"

        # Use LLM generate_text for transliteration
        if direction == "to_roman":
            prompt = f"""Transliterate the following Nepali text from Devanagari script to Roman script.
Provide ONLY the transliteration, without any explanations.

Text: {text}

Transliteration:"""
            result = await self.llm_provider.generate_text(
                prompt=prompt,
                system_prompt="You are a transliteration expert for Nepali language.",
                temperature=0.3,
            )
            return result.strip()
        elif direction == "to_devanagari":
            prompt = f"""Transliterate the following text from Roman script to Devanagari (Nepali) script.
Provide ONLY the transliteration, without any explanations.

Text: {text}

Transliteration:"""
            result = await self.llm_provider.generate_text(
                prompt=prompt,
                system_prompt="You are a transliteration expert for Nepali language.",
                temperature=0.3,
            )
            return result.strip()
        else:
            return text

    async def _translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text between languages using LLM.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        lang_names = {
            "en": "English",
            "ne": "Nepali",
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        prompt = f"""Translate the following text from {source_name} to {target_name}.
Provide ONLY the translation, without any explanations or additional text.

Text to translate:
{text}

Translation:"""

        translation = await self.llm_provider.generate_text(
            prompt=prompt,
            system_prompt=f"You are a professional translator specializing in {source_name} to {target_name} translation.",
            temperature=0.3,
        )

        return translation.strip()

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text.

        Args:
            text: The text to analyze

        Returns:
            Language code: "ne" for Nepali, "en" for English
        """
        return self.language_detector.detect(text)
