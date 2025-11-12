# nes/services/scraping/providers/openai.py

import json
import logging
import os
from typing import Any, Dict, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider for data extraction and normalization using Structured Outputs.

    Environment variables:
        OPENAI_API_KEY: Required. The API key for OpenAI or compatible endpoint.
        OPENAI_BASE_URL: Optional. Custom API endpoint base URL (for self-hosted or proxy setups).
        OPENAI_MODEL: Optional. Overrides the default model_id (e.g., 'gpt-4o-mini').
    """

    def __init__(
        self,
        model_id: str = "gpt-4o-2024-08-06",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        api_key: Optional[str] = None,
    ):
        """Initialize the OpenAI provider.

        Args:
            model_id: OpenAI model identifier (default “gpt-4o-2024-08-06”)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            api_key: OpenAI API key (optional, uses env if not provided)
        """

        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("The 'openai' package is not installed. ")

        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY environment variable must be set")

        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            self.client = AsyncOpenAI(api_key=key, base_url=base_url)
        else:
            self.client = AsyncOpenAI(api_key=key)

        model_env = os.getenv("OPENAI_MODEL")
        if model_env:
            model_id = model_env

        super().__init__(
            provider_name="openai",
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        self.top_p = top_p

        logger.info(
            f"OpenAIProvider initialized: model={model_id}, max_tokens={max_tokens}, temperature={temperature}, top_p={top_p}"
        )

    async def _generate_text_impl(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using OpenAI model.

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt for context
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            Generated text response
        """
        max_toks = max_tokens or self.max_tokens

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"Invoking OpenAI model: {self.model_id}")

        resp = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            max_tokens=max_toks,
        )

        text = resp.choices[0].message.content
        logger.debug(f"Generated {len(text)} characters")

        return text

    async def _extract_structured_data_impl(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str,
    ) -> Dict[str, Any]:
        """Extract structured data from text using the LLM with Structured Outputs.

        Args:
            text: The text to extract data from
            schema: JSON‐schema describing the expected output structure
            instructions: Instructions for the extraction task

        Returns:
            Extracted structured data as a dict
        """
        # Build the messages
        messages = [
            {
                "role": "system",
                "content": "You are a data extraction assistant. Extract structured information.",
            },
            {"role": "user", "content": f"{instructions}\n\nText to analyze:\n{text}"},
        ]

        logger.debug("Making structured output call with schema: %s", schema)

        resp = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=1,
            top_p=1,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ExtractionSchema",
                    "schema": {**schema, "additionalProperties": False},
                    "strict": True,
                },
            },
        )

        # Extract content: parse JSON directly
        content = resp.choices[0].message.content
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON from OpenAI response: {e}, content: {content}"
            )
            return {}

        return data

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text between languages using the model (via structured output optional).

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., "en", "ne")
            target_lang: Target language code

        Returns:
            Translated text
        """
        lang_names = {"en": "English", "ne": "Nepali"}
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        messages = [
            {
                "role": "system",
                "content": f"You are a professional translator from {source_name} to {target_name}.",
            },
            {
                "role": "user",
                "content": f"Translate the following text from {source_name} to {target_name} without any explanation:\n\n{text}",
            },
        ]

        resp = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=1,
            top_p=1,
        )

        translation = resp.choices[0].message.content.strip()
        return translation

    def get_token_usage(self) -> Dict[str, int]:
        """Token usage tracking not supported directly by openai python SDK in async mode."""
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def reset_token_usage(self) -> None:
        """Reset token usage counters (no‐op)."""
        pass
