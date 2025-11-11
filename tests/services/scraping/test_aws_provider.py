"""Tests for AWS Bedrock Provider.

These tests verify the AWS Bedrock provider implementation for LLM-powered
data extraction and normalization tasks.
"""

import json
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock boto3 before importing the provider
sys.modules["boto3"] = MagicMock()


class TestAWSBedrockProviderInitialization:
    """Test AWS Bedrock provider initialization."""

    def test_provider_initialization_default(self):
        """Test provider initialization with default settings."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()

            assert provider is not None
            assert provider.region_name == "us-east-1"
            assert (
                provider.model_id == "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
            )
            assert provider.model_family == "claude"

    def test_provider_initialization_custom_region(self):
        """Test provider initialization with custom region."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider(region_name="us-west-2")

            assert provider.region_name == "us-west-2"

    def test_provider_initialization_custom_model(self):
        """Test provider initialization with custom model."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider(
                model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"
            )

            assert (
                provider.model_id == "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
            )
            assert provider.model_family == "claude"

    def test_provider_initialization_invalid_model(self):
        """Test that invalid model raises ValueError."""
        with patch("boto3.Session"):
            from nes.services.scraping.providers import AWSBedrockProvider

            with pytest.raises(ValueError, match="Unsupported model"):
                AWSBedrockProvider(model_id="invalid-model-id")

    def test_provider_initialization_with_credentials(self):
        """Test provider initialization with explicit credentials."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider(
                aws_access_key_id="AKIA...",
                aws_secret_access_key="secret...",
            )

            assert provider is not None
            # Verify Session was called with credentials
            mock_session.assert_called_once()


class TestAWSBedrockProviderTextGeneration:
    """Test text generation capabilities."""

    @pytest.mark.asyncio
    async def test_generate_text_claude(self):
        """Test text generation with Claude model."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            # Mock Bedrock response
            mock_response = {
                "body": Mock(
                    read=lambda: json.dumps(
                        {
                            "content": [{"text": "Generated text response"}],
                            "usage": {"input_tokens": 10, "output_tokens": 5},
                        }
                    ).encode()
                )
            }
            mock_client.invoke_model.return_value = mock_response

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()
            result = await provider.generate_text(prompt="Test prompt")

            assert result == "Generated text response"
            assert provider.total_input_tokens == 10
            assert provider.total_output_tokens == 5

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            mock_response = {
                "body": Mock(
                    read=lambda: json.dumps(
                        {
                            "content": [{"text": "Response with system context"}],
                            "usage": {"input_tokens": 15, "output_tokens": 8},
                        }
                    ).encode()
                )
            }
            mock_client.invoke_model.return_value = mock_response

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()
            result = await provider.generate_text(
                prompt="User prompt", system_prompt="You are a helpful assistant"
            )

            assert result == "Response with system context"

    @pytest.mark.asyncio
    async def test_generate_text_custom_params(self):
        """Test text generation with custom parameters."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            mock_response = {
                "body": Mock(
                    read=lambda: json.dumps(
                        {
                            "content": [{"text": "Custom params response"}],
                            "usage": {"input_tokens": 20, "output_tokens": 10},
                        }
                    ).encode()
                )
            }
            mock_client.invoke_model.return_value = mock_response

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()
            result = await provider.generate_text(
                prompt="Test prompt", max_tokens=1000, temperature=0.5
            )

            assert result == "Custom params response"


class TestAWSBedrockProviderStructuredExtraction:
    """Test structured data extraction."""

    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test extracting structured data from text."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            # Mock response with JSON
            json_response = {"name": "Ram Chandra Poudel", "position": "President"}
            mock_response = {
                "body": Mock(
                    read=lambda: json.dumps(
                        {
                            "content": [{"text": json.dumps(json_response)}],
                            "usage": {"input_tokens": 20, "output_tokens": 10},
                        }
                    ).encode()
                )
            }
            mock_client.invoke_model.return_value = mock_response

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "position": {"type": "string"},
                },
            }

            result = await provider.extract_structured_data(
                text="Ram Chandra Poudel is the President of Nepal.",
                schema=schema,
                instructions="Extract person name and position",
            )

            assert result["name"] == "Ram Chandra Poudel"
            assert result["position"] == "President"

    @pytest.mark.asyncio
    async def test_extract_structured_data_with_markdown(self):
        """Test extracting JSON from markdown-formatted response."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            # Mock response with markdown formatting
            json_data = {"name": "Test Person", "role": "Politician"}
            markdown_response = f"```json\n{json.dumps(json_data)}\n```"
            mock_response = {
                "body": Mock(
                    read=lambda: json.dumps(
                        {
                            "content": [{"text": markdown_response}],
                            "usage": {"input_tokens": 15, "output_tokens": 8},
                        }
                    ).encode()
                )
            }
            mock_client.invoke_model.return_value = mock_response

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()
            result = await provider.extract_structured_data(
                text="Test text", schema={}, instructions="Extract data"
            )

            assert result["name"] == "Test Person"
            assert result["role"] == "Politician"


class TestAWSBedrockProviderTokenTracking:
    """Test token usage tracking."""

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self):
        """Test that token usage is tracked correctly."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            mock_response = {
                "body": Mock(
                    read=lambda: json.dumps(
                        {
                            "content": [{"text": "Response"}],
                            "usage": {"input_tokens": 100, "output_tokens": 50},
                        }
                    ).encode()
                )
            }
            mock_client.invoke_model.return_value = mock_response

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()

            # Make multiple calls
            await provider.generate_text(prompt="Test 1")
            await provider.generate_text(prompt="Test 2")

            usage = provider.get_token_usage()

            assert usage["input_tokens"] == 200
            assert usage["output_tokens"] == 100
            assert usage["total_tokens"] == 300

    def test_reset_token_usage(self):
        """Test resetting token usage counters."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client

            from nes.services.scraping.providers import AWSBedrockProvider

            provider = AWSBedrockProvider()
            provider.total_input_tokens = 100
            provider.total_output_tokens = 50

            provider.reset_token_usage()

            usage = provider.get_token_usage()
            assert usage["total_tokens"] == 0
