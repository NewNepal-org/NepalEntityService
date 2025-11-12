"""Tests for Google Vertex AI Provider."""

import json
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock google-cloud-aiplatform before importing
sys.modules["vertexai"] = MagicMock()
sys.modules["vertexai.generative_models"] = MagicMock()


class TestGoogleVertexAIProviderInitialization:
    """Test Google Vertex AI provider initialization."""

    def test_provider_initialization_default(self):
        """Test provider initialization with default settings."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ):
            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")

            assert provider.project_id == "test-project"
            assert provider.location == "us-central1"
            assert provider.model_id == "gemini-2.5-flash"
            assert provider.model_family == "gemini"

    def test_provider_initialization_custom_location(self):
        """Test provider initialization with custom location."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ):
            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(
                project_id="test-project", location="europe-west1"
            )

            assert provider.location == "europe-west1"

    def test_provider_initialization_custom_model(self):
        """Test provider initialization with custom model."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ):
            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(
                project_id="test-project", model_id="gemini-2.5-pro"
            )

            assert provider.model_id == "gemini-2.5-pro"
            assert provider.model_family == "gemini"

    def test_provider_initialization_invalid_model(self):
        """Test that invalid model raises ValueError."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ):
            from nes.services.scraping.providers import GoogleVertexAIProvider

            with pytest.raises(ValueError, match="Unsupported model"):
                GoogleVertexAIProvider(
                    project_id="test-project", model_id="invalid-model"
                )

    def test_provider_initialization_with_credentials(self):
        """Test provider initialization with credentials path."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ), patch("os.environ", {}):
            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(
                project_id="test-project", credentials_path="/path/to/key.json"
            )

            assert provider is not None


class TestGoogleVertexAIProviderTextGeneration:
    """Test text generation capabilities."""

    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test text generation with Gemini model."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ) as mock_model_class:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Generated text response"
            mock_response.usage_metadata = Mock(
                prompt_token_count=10, candidates_token_count=5
            )
            mock_chat.send_message.return_value = mock_response
            mock_client = Mock()
            mock_client.start_chat.return_value = mock_chat
            mock_model_class.return_value = mock_client

            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")
            result = await provider.generate_text(prompt="Test prompt")

            assert result == "Generated text response"
            assert provider.total_input_tokens == 10
            assert provider.total_output_tokens == 5

    @pytest.mark.asyncio
    async def test_generate_text_with_system_prompt(self):
        """Test text generation with system prompt."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ) as mock_model_class:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Response with system context"
            mock_response.usage_metadata = Mock(
                prompt_token_count=15, candidates_token_count=8
            )
            mock_chat.send_message.return_value = mock_response
            mock_client = Mock()
            mock_client.start_chat.return_value = mock_chat
            mock_model_class.return_value = mock_client

            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")
            result = await provider.generate_text(
                prompt="User prompt", system_prompt="You are a helpful assistant"
            )

            assert result == "Response with system context"

    @pytest.mark.asyncio
    async def test_generate_text_custom_params(self):
        """Test text generation with custom parameters."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ) as mock_model_class:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Custom params response"
            mock_response.usage_metadata = Mock(
                prompt_token_count=20, candidates_token_count=10
            )
            mock_chat.send_message.return_value = mock_response
            mock_client = Mock()
            mock_client.start_chat.return_value = mock_chat
            mock_model_class.return_value = mock_client

            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")
            result = await provider.generate_text(
                prompt="Test prompt", max_tokens=1000, temperature=0.5
            )

            assert result == "Custom params response"


class TestGoogleVertexAIProviderStructuredExtraction:
    """Test structured data extraction."""

    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test extracting structured data from text."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ) as mock_model_class:
            mock_client = Mock()
            json_response = {"name": "Harka Sampang", "position": "Mayor"}
            mock_response = Mock()
            mock_response.text = json.dumps(json_response)
            mock_response.usage_metadata = Mock(
                prompt_token_count=20, candidates_token_count=10
            )
            mock_client.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_client

            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "position": {"type": "string"},
                },
            }

            result = await provider.extract_structured_data(
                text="Harka Sampang is the Mayor of Dharan.",
                schema=schema,
                instructions="Extract person name and position",
            )

            assert result["name"] == "Harka Sampang"
            assert result["position"] == "Mayor"

    @pytest.mark.asyncio
    async def test_extract_structured_data_with_schema(self):
        """Test extracting structured data with schema validation."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ) as mock_model_class:
            mock_client = Mock()
            json_data = {"name": "Rabindra Mishra", "role": "Politician"}
            mock_response = Mock()
            mock_response.text = json.dumps(json_data)
            mock_response.usage_metadata = Mock(
                prompt_token_count=15, candidates_token_count=8
            )
            mock_client.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_client

            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                },
            }
            result = await provider.extract_structured_data(
                text="Test text", schema=schema, instructions="Extract data"
            )

            assert result["name"] == "Rabindra Mishra"
            assert result["role"] == "Politician"


class TestGoogleVertexAIProviderTokenTracking:
    """Test token usage tracking."""

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self):
        """Test that token usage is tracked correctly."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ) as mock_model_class:
            mock_chat = Mock()
            mock_response = Mock()
            mock_response.text = "Response"
            mock_response.usage_metadata = Mock(
                prompt_token_count=100, candidates_token_count=50
            )
            mock_chat.send_message.return_value = mock_response
            mock_client = Mock()
            mock_client.start_chat.return_value = mock_chat
            mock_model_class.return_value = mock_client

            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")

            await provider.generate_text(prompt="Test 1")
            await provider.generate_text(prompt="Test 2")

            usage = provider.get_token_usage()

            assert usage["input_tokens"] == 200
            assert usage["output_tokens"] == 100
            assert usage["total_tokens"] == 300

    def test_reset_token_usage(self):
        """Test resetting token usage counters."""
        with patch("vertexai.init"), patch(
            "vertexai.generative_models.GenerativeModel"
        ):
            from nes.services.scraping.providers import GoogleVertexAIProvider

            provider = GoogleVertexAIProvider(project_id="test-project")
            provider.total_input_tokens = 100
            provider.total_output_tokens = 50

            provider.reset_token_usage()

            usage = provider.get_token_usage()
            assert usage["total_tokens"] == 0
