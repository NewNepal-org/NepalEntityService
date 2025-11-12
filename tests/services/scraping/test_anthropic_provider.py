"""Tests for AnthropicProvider.

These tests verify the Anthropic provider implementation for LLM-powered
text generation, structured extraction, and translation tasks.
"""

import json
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock anthropic before importing the provider
mock_async_client = AsyncMock()
mock_async_client.messages.create = AsyncMock()

sys.modules["anthropic"] = MagicMock(
    AsyncAnthropic=MagicMock(return_value=mock_async_client),
    ResponseFormat=MagicMock(
        json_schema=MagicMock(side_effect=lambda **kwargs: kwargs)
    ),
)


class TestAnthropicProviderInitialization:
    """Test Anthropic provider initialization."""

    def test_provider_initialization_default(self):
        """Test provider initialization with default settings."""
        from nes.services.scraping.providers import AnthropicProvider

        provider = AnthropicProvider()
        assert provider is not None
        assert provider.model_id == "claude‑sonnet‑4‑5‑20250929"
        assert provider.model_family == "claude"

    def test_provider_initialization_invalid_model(self):
        """Test invalid model does not raise error but assigns model_id."""
        from nes.services.scraping.providers import AnthropicProvider

        provider = AnthropicProvider(model_id="invalid-model-id")
        assert provider.model_id == "invalid-model-id"


class TestAnthropicProviderTextGeneration:
    """Test text generation capabilities."""

    @pytest.mark.asyncio
    async def test_generate_text_basic(self):
        """Test basic text generation."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Generated text output")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()
        result = await provider.generate_text(prompt="Hello world")

        assert result == "Generated text output"
        assert provider.total_input_tokens == 10
        assert provider.total_output_tokens == 5

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test generation with system prompt."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Response with system")]
        mock_response.usage = Mock(input_tokens=12, output_tokens=6)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()
        result = await provider.generate_text(
            prompt="Test", system_prompt="You are a helpful assistant"
        )

        assert result == "Response with system"
        assert provider.total_input_tokens == 12
        assert provider.total_output_tokens == 6

    @pytest.mark.asyncio
    async def test_generate_text_custom_params(self):
        """Test generation with custom temperature and max tokens."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Custom param response")]
        mock_response.usage = Mock(input_tokens=15, output_tokens=8)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()
        result = await provider.generate_text(
            prompt="Something", max_tokens=1000, temperature=0.5
        )

        assert result == "Custom param response"
        assert provider.total_input_tokens == 15
        assert provider.total_output_tokens == 8


class TestAnthropicProviderStructuredExtraction:
    """Test structured data extraction."""

    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test extracting structured data from text."""
        from nes.services.scraping.providers import AnthropicProvider

        json_response = {"name": "Pushpa Kamal Dahal", "position": "Prime Minister"}
        mock_response = AsyncMock()
        mock_response.content = [
            SimpleNamespace(
                type="tool_use", name="structured_extraction", input=json_response
            )
        ]
        mock_response.usage = Mock(input_tokens=20, output_tokens=10)
        mock_async_client.messages.create = AsyncMock(return_value=mock_response)

        provider = AnthropicProvider()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "position": {"type": "string"},
            },
        }

        result = await provider.extract_structured_data(
            text="Pushpa Kamal Dahal is the Prime Minister of Nepal.",
            schema=schema,
            instructions="Extract person name and position.",
        )

        assert result["name"] == "Pushpa Kamal Dahal"
        assert result["position"] == "Prime Minister"

    @pytest.mark.asyncio
    async def test_extract_structured_data_json_error(self):
        """Test structured extraction when Claude returns invalid JSON."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="output_text", text="invalid json")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()
        schema = {}
        result = await provider.extract_structured_data(
            text="Some text", schema=schema, instructions="Extract data"
        )
        assert result == {}


class TestAnthropicProviderTranslation:
    """Test translation functionality."""

    @pytest.mark.asyncio
    async def test_translate_nepali_to_english(self):
        """Test translating Nepali to English."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Ram Chandra Poudel")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()
        result = await provider.translate(
            text="राम चन्द्र पौडेल", source_lang="ne", target_lang="en"
        )
        assert result == "Ram Chandra Poudel"

    @pytest.mark.asyncio
    async def test_translate_english_to_nepali(self):
        """Test translating English to Nepali."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="राम चन्द्र पौडेल")]
        mock_response.usage = Mock(input_tokens=8, output_tokens=4)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()
        result = await provider.translate(
            text="Ram Chandra Poudel", source_lang="en", target_lang="ne"
        )
        assert result == "राम चन्द्र पौडेल"


class TestAnthropicProviderTokenTracking:
    """Test token usage tracking."""

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self):
        """Test cumulative token tracking."""
        from nes.services.scraping.providers import AnthropicProvider

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Hello")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=25)
        mock_async_client.messages.create.return_value = mock_response

        provider = AnthropicProvider()

        await provider.generate_text(prompt="Test 1")
        await provider.generate_text(prompt="Test 2")

        usage = provider.get_token_usage()
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["total_tokens"] == 150

    def test_reset_token_usage(self):
        """Test resetting token usage counters."""
        from nes.services.scraping.providers import AnthropicProvider

        provider = AnthropicProvider()
        provider.total_input_tokens = 100
        provider.total_output_tokens = 50

        provider.reset_token_usage()

        usage = provider.get_token_usage()
        assert usage["total_tokens"] == 0
