"""Tests for Mock LLM Provider.

These tests verify the mock provider implementation for testing and development.
"""

import json

import pytest


class TestMockProviderInitialization:
    """Test mock provider initialization."""

    def test_provider_initialization(self):
        """Test provider initialization with defaults."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()

        assert provider is not None
        assert provider.provider_name == "mock"
        assert provider.model_id == "mock-model-v1"

    def test_provider_initialization_custom_params(self):
        """Test provider initialization with custom parameters."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider(max_tokens=4096, temperature=0.5)

        assert provider.max_tokens == 4096
        assert provider.temperature == 0.5


class TestMockProviderTextGeneration:
    """Test text generation capabilities."""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        result = await provider.generate_text(prompt="Hello world")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_text_translation(self):
        """Test text generation for translation."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        result = await provider.generate_text(prompt="Translate: राम चन्द्र पौडेल")

        # Mock provider translates Nepali to English
        assert result == "Ram Chandra Poudel"

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        result = await provider.generate_text(
            prompt="Test prompt", system_prompt="You are a helpful assistant"
        )

        assert result is not None
        assert isinstance(result, str)


class TestMockProviderStructuredExtraction:
    """Test structured data extraction."""

    @pytest.mark.asyncio
    async def test_extract_structured_data_known_entity(self):
        """Test extracting data for known entity."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "position": {"type": "string"}},
        }

        result = await provider.extract_structured_data(
            text="Ram Chandra Poudel is the President of Nepal.",
            schema=schema,
            instructions="Extract person information",
        )

        assert result is not None
        assert "name" in result
        assert result["name"] == "Ram Chandra Poudel"

    @pytest.mark.asyncio
    async def test_extract_structured_data_unknown_entity(self):
        """Test extracting data for unknown entity."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        result = await provider.extract_structured_data(
            text="Some unknown person is a politician.",
            schema=schema,
            instructions="Extract person information",
        )

        assert result is not None
        assert "name" in result


class TestMockProviderTokenTracking:
    """Test token usage tracking."""

    def test_token_usage_returns_zeros(self):
        """Test that mock provider returns zero token usage."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        usage = provider.get_token_usage()

        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0
        assert usage["total_tokens"] == 0

    def test_reset_token_usage(self):
        """Test resetting token usage (no-op for mock)."""
        from nes.services.scraping.providers import MockLLMProvider

        provider = MockLLMProvider()
        provider.reset_token_usage()  # Should not raise

        usage = provider.get_token_usage()
        assert usage["total_tokens"] == 0


class TestMockProviderIntegration:
    """Test mock provider integration with scraping service."""

    @pytest.mark.asyncio
    async def test_service_with_mock_provider_instance(self):
        """Test using mock provider instance with scraping service."""
        from nes.services.scraping import ScrapingService
        from nes.services.scraping.providers import MockLLMProvider

        # Create provider instance
        provider = MockLLMProvider()

        # Create service with provider instance
        service = ScrapingService(llm_provider=provider)

        assert service is not None
        assert service.provider is provider
        assert service.llm_provider_name == "mock"

    @pytest.mark.asyncio
    async def test_service_requires_provider(self):
        """Test that service requires an explicit provider."""
        from nes.services.scraping import ScrapingService
        from nes.services.scraping.providers import MockLLMProvider

        # Create service with explicit provider
        provider = MockLLMProvider()
        service = ScrapingService(llm_provider=provider)

        assert service is not None
        assert service.llm_provider_name == "mock"
        assert service.provider is provider
