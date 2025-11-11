"""Tests for translation service bulk_translate method.

Tests verify bulk translation functionality for efficient batch processing.
"""

import pytest


class TestBulkTranslate:
    """Test bulk translation functionality."""

    @pytest.mark.asyncio
    async def test_bulk_translate_empty_list(self):
        """Test bulk translate with empty list returns empty dict."""
        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        translator = Translator(llm_provider=provider)

        result = await translator.bulk_translate(
            texts=[], target_lang="en", source_lang="ne"
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_bulk_translate_nepali_to_english(self):
        """Test bulk translate from Nepali to English."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(
            return_value="1. Ram Chandra Poudel\n2. Nepali Congress"
        )

        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल", "नेपाली कांग्रेस"]
        result = await translator.bulk_translate(
            texts=texts, target_lang="en", source_lang="ne"
        )

        assert result["राम चन्द्र पौडेल"] == "Ram Chandra Poudel"
        assert result["नेपाली कांग्रेस"] == "Nepali Congress"

    @pytest.mark.asyncio
    async def test_bulk_translate_english_to_nepali(self):
        """Test bulk translate from English to Nepali."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(
            return_value="1. राम चन्द्र पौडेल\n2. नेपाली कांग्रेस"
        )

        translator = Translator(llm_provider=provider)

        texts = ["Ram Chandra Poudel", "Nepali Congress"]
        result = await translator.bulk_translate(
            texts=texts, target_lang="ne", source_lang="en"
        )

        assert result["Ram Chandra Poudel"] == "राम चन्द्र पौडेल"
        assert result["Nepali Congress"] == "नेपाली कांग्रेस"

    @pytest.mark.asyncio
    async def test_bulk_translate_auto_detect_source(self):
        """Test bulk translate with auto-detected source language."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(
            return_value="1. Ram Chandra Poudel\n2. Nepali Congress"
        )

        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल", "नेपाली कांग्रेस"]
        result = await translator.bulk_translate(texts=texts, target_lang="en")

        assert result["राम चन्द्र पौडेल"] == "Ram Chandra Poudel"
        assert result["नेपाली कांग्रेस"] == "Nepali Congress"

    @pytest.mark.asyncio
    async def test_bulk_translate_same_language_returns_identity(self):
        """Test bulk translate with same source and target returns identity mapping."""
        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल", "नेपाली कांग्रेस"]
        result = await translator.bulk_translate(
            texts=texts, target_lang="ne", source_lang="ne"
        )

        assert result == {
            "राम चन्द्र पौडेल": "राम चन्द्र पौडेल",
            "नेपाली कांग्रेस": "नेपाली कांग्रेस",
        }

    @pytest.mark.asyncio
    async def test_bulk_translate_single_text(self):
        """Test bulk translate with single text."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(return_value="1. Ram Chandra Poudel")

        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल"]
        result = await translator.bulk_translate(
            texts=texts, target_lang="en", source_lang="ne"
        )

        assert result["राम चन्द्र पौडेल"] == "Ram Chandra Poudel"

    @pytest.mark.asyncio
    async def test_bulk_translate_multiple_texts(self):
        """Test bulk translate with multiple texts."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(
            return_value="1. Harka Sampang\n2. Rabindra Mishra\n3. Rastriya Swatantra Party"
        )

        translator = Translator(llm_provider=provider)

        texts = ["हर्क साम्पाङ", "रवीन्द्र मिश्र", "राष्ट्रिय स्वतन्त्र पार्टी"]
        result = await translator.bulk_translate(
            texts=texts, target_lang="en", source_lang="ne"
        )

        assert result["हर्क साम्पाङ"] == "Harka Sampang"
        assert result["रवीन्द्र मिश्र"] == "Rabindra Mishra"
        assert result["राष्ट्रिय स्वतन्त्र पार्टी"] == "Rastriya Swatantra Party"

    @pytest.mark.asyncio
    async def test_bulk_translate_handles_different_numbering_formats(self):
        """Test bulk translate handles various numbering formats in response."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        # Test different numbering formats: "1. ", "2) ", "3:", "4 "
        provider.generate_text = AsyncMock(
            return_value="1. Ram Chandra Poudel\n2) Nepali Congress\n3: Harka Sampang\n4 Rastriya Swatantra Party"
        )

        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल", "नेपाली कांग्रेस", "हर्क साम्पाङ", "राष्ट्रिय स्वतन्त्र पार्टी"]
        result = await translator.bulk_translate(
            texts=texts, target_lang="en", source_lang="ne"
        )

        assert result["राम चन्द्र पौडेल"] == "Ram Chandra Poudel"
        assert result["नेपाली कांग्रेस"] == "Nepali Congress"
        assert result["हर्क साम्पाङ"] == "Harka Sampang"
        assert result["राष्ट्रिय स्वतन्त्र पार्टी"] == "Rastriya Swatantra Party"

    @pytest.mark.asyncio
    async def test_bulk_translate_prompt_format(self):
        """Test bulk translate generates correct prompt format."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(
            return_value="1. Ram Chandra Poudel\n2. Nepali Congress"
        )

        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल", "नेपाली कांग्रेस"]
        await translator.bulk_translate(texts=texts, target_lang="en", source_lang="ne")

        # Verify the prompt was called with correct format
        call_args = provider.generate_text.call_args
        prompt = call_args.kwargs["prompt"]

        assert "Translate the following 2 texts from Nepali to English" in prompt
        assert "1. राम चन्द्र पौडेल" in prompt
        assert "2. नेपाली कांग्रेस" in prompt
        assert "Provide ONLY the translations" in prompt

    @pytest.mark.asyncio
    async def test_bulk_translate_uses_correct_temperature(self):
        """Test bulk translate uses temperature 0.3 for consistency."""
        from unittest.mock import AsyncMock

        from nes.services.scraping.providers import MockLLMProvider
        from nes.services.scraping.translation import Translator

        provider = MockLLMProvider()
        provider.generate_text = AsyncMock(return_value="1. Ram Chandra Poudel")

        translator = Translator(llm_provider=provider)

        texts = ["राम चन्द्र पौडेल"]
        await translator.bulk_translate(texts=texts, target_lang="en", source_lang="ne")

        call_args = provider.generate_text.call_args
        assert call_args.kwargs["temperature"] == 0.3
