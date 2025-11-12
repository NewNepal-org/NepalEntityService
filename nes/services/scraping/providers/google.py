"""Google Cloud Vertex AI LLM Provider for the Scraping Service.

This module provides integration with Google Cloud Vertex AI for LLM-powered
data extraction, normalization, and translation tasks.

Google Cloud Vertex AI Support:
    - Gemini models (Gemini 2.5 Pro, Flash)
    - PaLM 2 models
    - Codey models

Features:
    - Async API calls for better performance
    - Token usage tracking
    - Structured output parsing
    - Error handling and fallback mechanisms

Configuration:
    Requires Google Cloud credentials configured via:
    - Environment variable (GOOGLE_APPLICATION_CREDENTIALS)
    - Service account key file
    - Application Default Credentials (ADC)
"""

import asyncio
import json
import logging
import time
import warnings
from typing import Any, Dict, Optional

from .base import BaseLLMProvider

# Suppress Vertex AI deprecation warning
warnings.filterwarnings(
    "ignore",
    message="This feature is deprecated as of June 24, 2025",
    category=UserWarning,
    module="vertexai.generative_models._generative_models",
)

logger = logging.getLogger(__name__)


class GoogleVertexAIProvider(BaseLLMProvider):
    """Google Cloud Vertex AI LLM provider for data extraction and normalization.

    Attributes:
        project_id: Google Cloud project ID
        location: Google Cloud region
        model_id: Vertex AI model identifier
        client: Vertex AI client
    """

    SUPPORTED_MODELS = {
        "gemini-2.5-pro": {
            "family": "gemini",
            "max_tokens": 65_535,
        },
        "gemini-2.5-flash": {
            "family": "gemini",
            "max_tokens": 65_535,
        },
    }

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_id: str = "gemini-2.5-flash",
        max_tokens: int = 65_535,
        temperature: float = 0.7,
        credentials_path: Optional[str] = None,
        enable_cache: bool = True,
    ):
        """Initialize the Google Vertex AI provider.

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region (default: "us-central1")
            model_id: Vertex AI model identifier
            max_tokens: Maximum tokens to generate (default: 2048)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            credentials_path: Path to service account key file (optional)
            enable_cache: Enable response caching (default: True)

        Raises:
            ValueError: If model_id is not supported
            ImportError: If google-cloud-aiplatform is not installed
        """
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform is required for Google Vertex AI provider. "
                "Install it with: pip install google-cloud-aiplatform"
            )

        if model_id not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model_id}. "
                f"Supported models: {list(self.SUPPORTED_MODELS.keys())}"
            )

        super().__init__(
            provider_name="google_vertexai",
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            enable_cache=enable_cache,
        )

        self.project_id = project_id
        self.location = location
        self.model_config = self.SUPPORTED_MODELS[model_id]
        self.model_family = self.model_config["family"]

        # Initialize Vertex AI with credentials from environment
        import os

        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        vertexai.init(project=project_id, location=location)
        self.client = GenerativeModel(model_id)

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests

        logger.info(
            f"GoogleVertexAIProvider initialized: project={project_id}, "
            f"location={location}, model={model_id}"
        )

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    async def _retry_with_backoff(self, func, *args, max_retries: int = 5, **kwargs):
        """Retry function with exponential backoff on rate limit errors.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result from func
        """
        for attempt in range(max_retries):
            try:
                await self._rate_limit()
                return await asyncio.to_thread(func, *args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "ResourceExhausted" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2**attempt) + (asyncio.get_event_loop().time() % 1)
                        logger.warning(
                            f"Rate limit hit, retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Max retries reached for rate limit error")
                        raise
                else:
                    raise

    async def _generate_text_impl(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using the LLM (implementation).

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt for context
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            Generated text response
        """
        try:
            from vertexai.generative_models import GenerationConfig, GenerativeModel

            max_tokens = max_tokens or self.max_tokens
            temperature = temperature if temperature is not None else self.temperature

            config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            model = GenerativeModel(
                self.model_id,
                system_instruction=system_prompt if system_prompt else None,
            )

            logger.debug(f"Invoking Vertex AI chat: {self.model_id}")

            chat = model.start_chat()
            response = await self._retry_with_backoff(
                chat.send_message,
                prompt,
                generation_config=config,
            )

            text = response.text

            self.total_input_tokens += response.usage_metadata.prompt_token_count
            self.total_output_tokens += response.usage_metadata.candidates_token_count

            logger.debug(f"Generated {len(text)} characters")

            return text

        except Exception as e:
            logger.error(f"Error generating text with Vertex AI: {e}", exc_info=True)
            raise

    async def _extract_structured_data_impl(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str,
    ) -> Dict[str, Any]:
        """Extract structured data from text using the LLM (implementation).

        Args:
            text: The text to extract data from
            schema: JSON schema describing the expected output structure
            instructions: Instructions for the extraction task

        Returns:
            Extracted structured data as a dictionary

        Raises:
            json.JSONDecodeError: If the LLM response cannot be parsed as JSON
            Exception: If data extraction fails for any other reason
        """
        from vertexai.generative_models import GenerationConfig, GenerativeModel

        system_instruction = "You are a data extraction assistant. Extract structured information from text."

        config = GenerationConfig(
            max_output_tokens=self.max_tokens,
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=schema,
        )

        model = GenerativeModel(
            self.model_id,
            system_instruction=system_instruction,
        )

        prompt = f"{instructions}\n\nText to analyze:\n{text}"
        response = await self._retry_with_backoff(
            model.generate_content,
            prompt,
            generation_config=config,
        )

        # Track token usage
        self.total_input_tokens += response.usage_metadata.prompt_token_count
        self.total_output_tokens += response.usage_metadata.candidates_token_count

        # Parse and return JSON response
        if not response.text:
            logger.error("Empty response from LLM")
            raise ValueError("Empty response from LLM")

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response text: {response.text}")
            raise

    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage statistics.

        Returns:
            Dictionary with input_tokens, output_tokens, and total_tokens
        """
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        logger.debug("Token usage counters reset")
