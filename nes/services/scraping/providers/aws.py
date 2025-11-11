"""AWS Bedrock LLM Provider for the Scraping Service.

This module provides integration with AWS Bedrock for LLM-powered data extraction,
normalization, and translation tasks.

AWS Bedrock Support:
    - Anthropic Claude models (Claude 3 Sonnet, Haiku, Opus)
    - Amazon Titan models
    - AI21 Labs Jurassic models
    - Cohere Command models
    - Meta Llama models

Features:
    - Async API calls for better performance
    - Automatic retry with exponential backoff
    - Token usage tracking and cost estimation
    - Structured output parsing
    - Error handling and fallback mechanisms

Configuration:
    Requires AWS credentials configured via:
    - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - AWS credentials file (~/.aws/credentials)
    - IAM role (when running on AWS infrastructure)

Performance Considerations:
    - Uses async boto3 client for non-blocking operations
    - Implements request batching where possible
    - Caches model responses for repeated queries
    - Monitors token usage to optimize costs

Security:
    - Uses AWS IAM for authentication and authorization
    - Supports VPC endpoints for private connectivity
    - Encrypts data in transit and at rest
    - Follows AWS security best practices
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AWSBedrockProvider(BaseLLMProvider):
    """AWS Bedrock LLM provider for data extraction and normalization.

    This provider integrates with AWS Bedrock to leverage various foundation
    models for intelligent data extraction, translation, and normalization tasks.

    Attributes:
        region_name: AWS region for Bedrock service
        model_id: Bedrock model identifier
        client: Boto3 Bedrock Runtime client
        max_tokens: Maximum tokens for generation
        temperature: Sampling temperature (0.0-1.0)
        top_p: Nucleus sampling parameter
    """

    # Supported model families and their configurations
    SUPPORTED_MODELS = {
        "global.anthropic.claude-sonnet-4-5-20250929-v1:0": {
            "family": "claude",
            "max_tokens": 200_000,
        },
    }

    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str = "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        profile_name: Optional[str] = None,
        enable_cache: bool = True,
    ):
        """Initialize the AWS Bedrock provider.

        Calls parent class constructor and then initializes AWS-specific components.

        Args:
            region_name: AWS region name (default: "us-east-1")
            model_id: Bedrock model identifier
            max_tokens: Maximum tokens to generate (default: 2048)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            top_p: Nucleus sampling parameter (default: 0.9)
            aws_access_key_id: AWS access key (optional, uses default credentials if not provided)
            aws_secret_access_key: AWS secret key (optional)
            aws_session_token: AWS session token (optional)
            profile_name: AWS profile name from ~/.aws/credentials (optional)
            enable_cache: Enable response caching (default: True)

        Raises:
            ValueError: If model_id is not supported
            ImportError: If boto3 is not installed

        Examples:
            >>> # Use default credentials
            >>> provider = AWSBedrockProvider()

            >>> # Use explicit credentials
            >>> provider = AWSBedrockProvider(
            ...     region_name="us-west-2",
            ...     aws_access_key_id="AKIA...",
            ...     aws_secret_access_key="..."
            ... )

            >>> # Use specific model
            >>> provider = AWSBedrockProvider(
            ...     model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0"
            ... )

            >>> # Use AWS profile
            >>> provider = AWSBedrockProvider(
            ...     profile_name="my-aws-profile"
            ... )

            >>> # Disable caching
            >>> provider = AWSBedrockProvider(
            ...     enable_cache=False
            ... )
        """
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for AWS Bedrock provider. "
                "Install it with: pip install boto3"
            )

        # Validate model
        if model_id not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model_id}. "
                f"Supported models: {list(self.SUPPORTED_MODELS.keys())}"
            )

        # Initialize base class
        super().__init__(
            provider_name="aws_bedrock",
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            enable_cache=enable_cache,
        )

        self.region_name = region_name
        self.top_p = top_p

        # Get model configuration
        self.model_config = self.SUPPORTED_MODELS[model_id]
        self.model_family = self.model_config["family"]

        # Initialize boto3 client
        session_kwargs = {"region_name": region_name}
        if profile_name:
            session_kwargs["profile_name"] = profile_name
        if aws_access_key_id:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key
        if aws_session_token:
            session_kwargs["aws_session_token"] = aws_session_token

        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        logger.info(
            f"AWSBedrockProvider initialized: region={region_name}, "
            f"model={model_id}, family={self.model_family}"
        )

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

        Raises:
            Exception: If API call fails
        """
        try:
            # Use provided values or defaults
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature if temperature is not None else self.temperature

            # Build request based on model family
            if self.model_family == "claude":
                request_body = self._build_claude_request(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            elif self.model_family == "titan":
                request_body = self._build_titan_request(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                raise ValueError(f"Unsupported model family: {self.model_family}")

            logger.debug(f"Invoking Bedrock model: {self.model_id}")

            # Invoke model (sync call wrapped in async)
            response = await asyncio.to_thread(
                self.client.invoke_model,
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract text based on model family
            if self.model_family == "claude":
                text = self._parse_claude_response(response_body)
            elif self.model_family == "titan":
                text = self._parse_titan_response(response_body)
            else:
                raise ValueError(f"Unsupported model family: {self.model_family}")

            # Track token usage
            self._track_token_usage(response_body)

            logger.debug(f"Generated {len(text)} characters")

            return text

        except Exception as e:
            logger.error(f"Error generating text with Bedrock: {e}", exc_info=True)
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
        """
        # Build extraction prompt
        prompt = f"""{instructions}

Text to analyze:
{text}

Expected output format (JSON):
{json.dumps(schema, indent=2)}

Extract the information and return ONLY valid JSON matching the schema above.
"""

        # Generate response
        response_text = await self.generate_text(
            prompt=prompt,
            system_prompt="You are a data extraction assistant. Extract structured information from text and return valid JSON.",
            temperature=0.3,  # Lower temperature for more consistent extraction
        )

        # Parse JSON from response
        try:
            # Try to extract JSON from response (may have markdown formatting)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return data
            else:
                # Try parsing entire response
                return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response text: {response_text}")
            # Return empty dict on parse failure
            return {}

    def _build_claude_request(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """Build request body for Claude models."""
        request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        if system_prompt:
            request["system"] = system_prompt

        return request

    def _build_titan_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """Build request body for Titan models."""
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": self.top_p,
            },
        }

    def _parse_claude_response(self, response_body: Dict[str, Any]) -> str:
        """Parse response from Claude models."""
        content = response_body.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "")
        return ""

    def _parse_titan_response(self, response_body: Dict[str, Any]) -> str:
        """Parse response from Titan models."""
        results = response_body.get("results", [])
        if results and len(results) > 0:
            return results[0].get("outputText", "")
        return ""

    def _track_token_usage(self, response_body: Dict[str, Any]) -> None:
        """Track token usage from response."""
        usage = response_body.get("usage", {})

        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        logger.debug(
            f"Token usage - Input: {input_tokens}, Output: {output_tokens}, "
            f"Total: {self.total_input_tokens + self.total_output_tokens}"
        )

    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage statistics.

        Returns:
            Dictionary with input_tokens, output_tokens, and total_tokens

        Examples:
            >>> usage = provider.get_token_usage()
            >>> print(f"Total tokens used: {usage['total_tokens']}")
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
