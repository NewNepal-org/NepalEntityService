"""Base LLM Provider interface for the Scraping Service.

This module defines the abstract base class that all LLM providers must implement.
It ensures a consistent interface across different provider implementations.

Provider Responsibilities:
    - Text generation with configurable parameters (used for translation, transliteration, etc.)
    - Structured data extraction from unstructured text
    - Token usage tracking (optional but recommended)
    - Response caching for improved performance

Design Principles:
    - Async-first API for non-blocking operations
    - Consistent error handling across providers
    - Flexible configuration via provider-specific kwargs
    - Optional features (like token tracking) gracefully degrade
    - Caching handled transparently at the base layer
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must inherit from this class and implement the required
    abstract methods. This ensures a consistent interface across different
    provider implementations (AWS, OpenAI, Google, etc.).

    Attributes:
        provider_name: Human-readable name of the provider
        model_id: Identifier of the specific model being used
        max_tokens: Default maximum tokens for generation
        temperature: Default sampling temperature
    """

    def __init__(
        self,
        provider_name: str,
        model_id: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        enable_cache: bool = True,
        **kwargs,
    ):
        """Initialize the base provider.

        Args:
            provider_name: Human-readable name of the provider
            model_id: Identifier of the specific model
            max_tokens: Default maximum tokens for generation
            temperature: Default sampling temperature (0.0-1.0)
            enable_cache: Enable response caching (default: True)
            **kwargs: Provider-specific configuration options
        """
        self.provider_name = provider_name
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enable_cache = enable_cache
        self.config = kwargs

        # Cache for LLM responses
        self._cache: Dict[str, Any] = {}

        logger.info(
            f"Initialized {provider_name} provider with model={model_id}, "
            f"cache={'enabled' if enable_cache else 'disabled'}"
        )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using the LLM with automatic caching.

        This method handles caching automatically. Providers should implement
        _generate_text_impl instead.

        Args:
            prompt: The input prompt for text generation
            system_prompt: Optional system prompt for context/instructions
            max_tokens: Override default max_tokens for this request
            temperature: Override default temperature for this request

        Returns:
            Generated text as a string

        Raises:
            Exception: Provider-specific exceptions for API failures

        Examples:
            >>> provider = SomeProvider()
            >>> text = await provider.generate_text(
            ...     prompt="Translate: राम चन्द्र पौडेल",
            ...     system_prompt="You are a translator"
            ... )
        """
        # Check cache
        cache_key = self._get_cache_key(
            "generate_text", prompt, system_prompt, max_tokens, temperature
        )
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug("Returning cached response for generate_text")
            return cached

        # Call implementation
        result = await self._generate_text_impl(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Cache the result
        self._set_cache(cache_key, result)

        return result

    @abstractmethod
    async def _generate_text_impl(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using the LLM (implementation method).

        This is the core method that all providers must implement. It takes
        a prompt and returns generated text. Caching is handled by the base class.

        Args:
            prompt: The input prompt for text generation
            system_prompt: Optional system prompt for context/instructions
            max_tokens: Override default max_tokens for this request
            temperature: Override default temperature for this request

        Returns:
            Generated text as a string

        Raises:
            Exception: Provider-specific exceptions for API failures
        """
        pass

    async def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str,
    ) -> Dict[str, Any]:
        """Extract structured data from text using the LLM with automatic caching.

        This method handles caching automatically. Providers should implement
        _extract_structured_data_impl instead.

        Args:
            text: The text to extract data from
            schema: JSON schema describing the expected output structure
            instructions: Instructions for the extraction task

        Returns:
            Extracted structured data as a dictionary conforming to the schema

        Raises:
            Exception: Provider-specific exceptions for API failures

        Examples:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"type": "string"},
            ...         "position": {"type": "string"}
            ...     }
            ... }
            >>> data = await provider.extract_structured_data(
            ...     text="Ram Chandra Poudel is the President.",
            ...     schema=schema,
            ...     instructions="Extract person name and position"
            ... )
        """
        # Check cache
        cache_key = self._get_cache_key(
            "extract_structured_data", text, str(schema), instructions
        )
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug("Returning cached response for extract_structured_data")
            return cached

        # Call implementation
        result = await self._extract_structured_data_impl(
            text=text, schema=schema, instructions=instructions
        )

        # Cache the result
        self._set_cache(cache_key, result)

        return result

    @abstractmethod
    async def _extract_structured_data_impl(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str,
    ) -> Dict[str, Any]:
        """Extract structured data from text using the LLM (implementation method).

        Providers must implement this method to extract structured information
        from unstructured text according to a provided schema. Caching is handled
        by the base class.

        Args:
            text: The text to extract data from
            schema: JSON schema describing the expected output structure
            instructions: Instructions for the extraction task

        Returns:
            Extracted structured data as a dictionary conforming to the schema

        Raises:
            Exception: Provider-specific exceptions for API failures
        """
        pass

    def get_token_usage(self) -> Dict[str, int]:
        """Get token usage statistics.

        Optional method that providers can override to track token usage.
        Default implementation returns zeros.

        Returns:
            Dictionary with input_tokens, output_tokens, and total_tokens

        Examples:
            >>> usage = provider.get_token_usage()
            >>> print(f"Total tokens: {usage['total_tokens']}")
        """
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    def reset_token_usage(self) -> None:
        """Reset token usage counters.

        Optional method that providers can override to reset usage tracking.
        Default implementation does nothing.
        """
        pass

    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments.

        Args:
            *args: Positional arguments to hash
            **kwargs: Keyword arguments to hash

        Returns:
            Cache key as a string
        """
        # Create a stable string representation
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "|".join(key_parts)

        # Hash for consistent key length
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            cache_key: The cache key

        Returns:
            Cached value or None if not found or cache disabled
        """
        if not self.enable_cache:
            return None
        return self._cache.get(cache_key)

    def _set_cache(self, cache_key: str, value: Any) -> None:
        """Set a value in cache.

        Args:
            cache_key: The cache key
            value: The value to cache
        """
        if self.enable_cache:
            self._cache[cache_key] = value

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(provider={self.provider_name}, model={self.model_id})"
