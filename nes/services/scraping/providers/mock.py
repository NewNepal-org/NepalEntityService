"""Mock LLM Provider for testing and development.

This module provides a mock LLM provider that simulates LLM behavior without
making actual API calls. It's useful for:
- Testing without API costs
- Development without API credentials
- Predictable, deterministic responses
- Fast execution without network latency

The mock provider uses simple pattern matching and templates to generate
responses that mimic real LLM behavior for common Nepal Entity Service tasks.
"""

import json
import logging
from typing import Any, Dict, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing and development.

    This provider simulates LLM behavior using pattern matching and templates.
    It provides deterministic responses for common tasks like translation,
    data extraction, and text generation.

    Attributes:
        provider_name: Always "mock"
        model_id: Always "mock-model-v1"
        response_templates: Dictionary of response templates for common tasks
    """

    def __init__(self, max_tokens: int = 2048, temperature: float = 0.7, **kwargs):
        """Initialize the mock provider.

        Args:
            max_tokens: Default maximum tokens (not enforced in mock)
            temperature: Default temperature (not used in mock)
            **kwargs: Additional configuration (ignored)

        Examples:
            >>> provider = MockLLMProvider()
            >>> text = await provider.generate_text("Hello")
        """
        super().__init__(
            provider_name="mock",
            model_id="mock-model-v1",
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        # Initialize response templates
        self.response_templates = self._initialize_templates()

        logger.info("MockLLMProvider initialized")

    def _initialize_templates(self) -> Dict[str, Any]:
        """Initialize response templates for common tasks.

        Returns:
            Dictionary of response templates
        """
        return {
            "translations": {
                # Nepali to English
                "राम चन्द्र पौडेल": "Ram Chandra Poudel",
                "नेपाली कांग्रेस": "Nepali Congress",
                "नेता": "leader",
                "हुन्": "is",
                "का": "of",
                "राम चन्द्र पौडेल नेपाली कांग्रेसका नेता हुन्।": "Ram Chandra Poudel is a leader of Nepali Congress.",
                # English to Nepali
                "Ram Chandra Poudel": "राम चन्द्र पौडेल",
                "Nepali Congress": "नेपाली कांग्रेस",
                "leader": "नेता",
                "is": "हुन्",
                "of": "का",
                "Ram Chandra Poudel is a leader of Nepali Congress.": "राम चन्द्र पौडेल नेपाली कांग्रेसका नेता हुन्।",
            },
            "entities": {
                "Ram Chandra Poudel": {
                    "name": "Ram Chandra Poudel",
                    "position": "President",
                    "party": "Nepali Congress",
                    "occupation": "politician",
                },
            },
        }

    async def _generate_text_impl(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using mock responses (implementation).

        Uses pattern matching to provide appropriate mock responses based
        on the prompt content.

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt (used for context)
            max_tokens: Ignored in mock implementation
            temperature: Ignored in mock implementation

        Returns:
            Mock generated text

        Examples:
            >>> provider = MockLLMProvider()
            >>> text = await provider.generate_text(
            ...     prompt="Translate: राम चन्द्र पौडेल"
            ... )
            >>> print(text)
            'Ram Chandra Poudel'
        """
        logger.debug(f"Mock generate_text called with prompt length: {len(prompt)}")

        # Check for translation requests
        if "translate" in prompt.lower():
            return self._handle_translation(prompt)

        # Check for extraction requests
        if "extract" in prompt.lower():
            return self._handle_extraction(prompt)

        # Default response
        return f"Mock response for: {prompt[:50]}..."

    async def _extract_structured_data_impl(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str,
    ) -> Dict[str, Any]:
        """Extract structured data using mock extraction (implementation).

        Uses pattern matching to extract common entity information.

        Args:
            text: The text to extract data from
            schema: JSON schema (used to determine output structure)
            instructions: Instructions (used for context)

        Returns:
            Mock extracted data conforming to schema

        Examples:
            >>> schema = {"properties": {"name": {}, "position": {}}}
            >>> data = await provider.extract_structured_data(
            ...     text="Ram Chandra Poudel is the President.",
            ...     schema=schema,
            ...     instructions="Extract person info"
            ... )
        """
        logger.debug(
            f"Mock extract_structured_data called for text length: {len(text)}"
        )

        # Check for known entities
        for entity_name, entity_data in self.response_templates["entities"].items():
            if entity_name in text:
                # Filter data based on schema properties
                if "properties" in schema:
                    filtered_data = {}
                    for prop in schema["properties"].keys():
                        if prop in entity_data:
                            filtered_data[prop] = entity_data[prop]
                    return filtered_data if filtered_data else entity_data
                return entity_data

        # Default extraction
        return {
            "name": "Unknown Person",
            "position": "Unknown",
        }

    def _handle_translation(self, prompt: str) -> str:
        """Handle translation requests in prompts.

        Args:
            prompt: The prompt containing translation request

        Returns:
            Translated text
        """
        # Extract text between "Text to translate:" and "Translation:"
        if "Text to translate:" in prompt:
            parts = prompt.split("Text to translate:")
            if len(parts) > 1:
                text_part = parts[1].split("Translation:")[0].strip()
                text_to_translate = text_part.strip()
            else:
                text_to_translate = prompt.split(":")[-1].strip()
        else:
            # Fallback: extract text after last colon
            text_to_translate = prompt.split(":")[-1].strip()

        # Check if it's in our templates
        if text_to_translate in self.response_templates["translations"]:
            return self.response_templates["translations"][text_to_translate]

        # Check for partial matches in templates
        for key, value in self.response_templates["translations"].items():
            if key in text_to_translate or text_to_translate in key:
                return value

        # Default translation
        return f"Translated: {text_to_translate}"

    def _handle_extraction(self, prompt: str) -> str:
        """Handle extraction requests in prompts.

        Args:
            prompt: The prompt containing extraction request

        Returns:
            JSON string with extracted data
        """
        # Check for known entities in prompt
        for entity_name, entity_data in self.response_templates["entities"].items():
            if entity_name in prompt:
                return json.dumps(entity_data, indent=2)

        # Default extraction
        return json.dumps({"name": "Unknown", "extracted": True}, indent=2)

    def get_token_usage(self) -> Dict[str, int]:
        """Get mock token usage.

        Returns zero usage since no actual API calls are made.

        Returns:
            Dictionary with zero token counts
        """
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    def reset_token_usage(self) -> None:
        """Reset token usage (no-op for mock provider)."""
        pass
