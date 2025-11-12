import logging
import os
from typing import Any, Dict, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude model provider.

    Environment variables:
    - ANTHROPIC_API_KEY (required): The API key for Anthropic or compatible endpoint.
    - ANTHROPIC_BASE_URL (optional): Custom API endpoint base URL (for self-hosted or proxy setups).
    - ANTHROPIC_MODEL_ID (optional): Overrides the default model_id (e.g., 'claude-3-5-haiku').
    """

    def __init__(
        self,
        model_id: str = "claude‑sonnet‑4‑5‑20250929",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        enable_cache: bool = True,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize the Anthropic provider."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic SDK is required. Install it with: pip install anthropic"
            )

        super().__init__(
            provider_name="anthropic",
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            enable_cache=enable_cache,
        )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = (
            base_url
            or os.getenv("ANTHROPIC_BASE_URL")
            or "https://api.anthropic.com/v1"
        )

        self.client = anthropic.AsyncAnthropic(
            api_key=self.api_key, base_url=self.base_url
        )
        self.model_family = "claude"

        # Track tokens
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        logger.info(f"AnthropicProvider initialized with model: {model_id}")

    async def _generate_text_impl(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using Claude models."""
        import anthropic

        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature

        try:
            messages = [{"role": "user", "content": prompt}]
            system = system_prompt or "You are a helpful assistant."

            logger.debug(f"Invoking Claude model: {self.model_id}")

            response = await self.client.messages.create(
                model=self.model_id,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )

            text = self._parse_claude_response(response)
            self._track_token_usage(response)

            logger.debug(f"Generated {len(text)} characters from Claude.")
            return text

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error from Anthropic: {e}", exc_info=True)
            raise

    async def _extract_structured_data_impl(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: str,
    ) -> Dict[str, Any]:
        """Extract structured JSON from text using Claude with tool-schema."""
        import anthropic

        # Build messages
        messages = [
            {
                "role": "user",
                "content": (f"{instructions}\n\n" f"Text to analyze:\n{text}"),
            }
        ]

        # Define the tool for structured extraction
        tool_name = "structured_extraction"
        tool = {
            "name": tool_name,
            "description": (
                "Returns a JSON object matching the given schema of properties."
            ),
            "input_schema": schema,
        }

        logger.debug(
            "Calling Claude tool-schema extraction with tool: %s, schema: %s",
            tool_name,
            schema,
        )

        try:
            response = await self.client.messages.create(
                model=self.model_id,
                messages=messages,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
                max_tokens=self.max_tokens,
                temperature=0.3,
            )

            # Track tokens usage
            self._track_token_usage(response)

            # Inspect content blocks for tool use
            for block in response.content:
                if (
                    getattr(block, "type", None) == "tool_use"
                    and getattr(block, "name", None) == tool_name
                ):
                    # The model selected the tool and provided inputs
                    return block.input  # Expect dictionary matching schema

            # No tool_use found
            logger.warning(
                "Claude response contained no tool_use block for structured extraction."
            )
            return {}

        except anthropic.APIError as e:
            logger.error(
                f"Anthropic API error during structured extraction: {e}", exc_info=True
            )
            return {}
        except Exception as e:
            logger.error(
                f"Unexpected error in structured extraction: {e}", exc_info=True
            )
            return {}

    def _parse_claude_response(self, response: Any) -> str:
        """Parse the message content from Anthropic response."""
        if hasattr(response, "content"):
            for block in response.content:
                if block.type == "text":
                    return block.text
        return ""

    def _track_token_usage(self, response: Any) -> None:
        """Track token usage from Anthropic response."""
        usage = getattr(response, "usage", None)
        if not usage:
            return

        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        logger.debug(
            f"Token usage - Input: {input_tokens}, Output: {output_tokens}, "
            f"Total: {self.total_input_tokens + self.total_output_tokens}"
        )

    def get_token_usage(self) -> Dict[str, int]:
        """Get cumulative token usage."""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }

    def reset_token_usage(self) -> None:
        """Reset token counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        logger.debug("Token usage counters reset.")

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Translate text between languages using Claude."""
        prompt = (
            f"Translate the following text from {source_lang} to {target_lang}.\n\n"
            f"Text:\n{text}"
        )

        # Use Claude text generation
        translated = await self._generate_text_impl(
            prompt=prompt,
            system_prompt=system_prompt or "You are a professional translator.",
            max_tokens=self.max_tokens,
            temperature=0.3,
        )

        return translated.strip()
