"""Translation CLI command for Nepal Entity Service.

Provides command-line translation between English and Nepali, supporting:
- Devanagari script (native Nepali)
- Romanized Nepali text
- Automatic language detection

Environment Variables:
    AWS_REGION: AWS region for Bedrock (default: us-east-1)
    AWS_BEDROCK_MODEL_ID: Model ID to use (default: global.anthropic.claude-sonnet-4-5-20250929-v1:0)
    AWS_PROFILE: AWS profile name (automatically picked up by boto3)
    AWS_ACCESS_KEY_ID: AWS access key (automatically picked up by boto3)
    AWS_SECRET_ACCESS_KEY: AWS secret key (automatically picked up by boto3)
    AWS_SESSION_TOKEN: AWS session token (automatically picked up by boto3)
"""

import asyncio
import sys

import click


def get_translation_service(provider_name, model_id, region_name):
    """Get or create translation service instance.

    Args:
        provider_name: Name of the LLM provider (currently only "aws" is supported)
        model_id: Model ID to use (None to use provider default)
        region_name: AWS region (None to use provider default)

    Returns:
        Translator instance configured with LLM provider

    Raises:
        ValueError: If an unsupported provider is specified
    """
    from nes.services.scraping import ScrapingService

    if provider_name == "aws":
        from nes.services.scraping.providers import AWSBedrockProvider

        # Set AWS-specific defaults
        # For AWS: default model is Claude Sonnet 4.5, default region is us-east-1
        aws_model_id = model_id or "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
        aws_region = region_name or "us-east-1"

        # AWS_PROFILE is automatically picked up by boto3
        provider = AWSBedrockProvider(
            region_name=aws_region,
            model_id=aws_model_id,
        )
    else:
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Currently only 'aws' is supported."
        )

    service = ScrapingService(llm_provider=provider)
    return service.translator


@click.command()
@click.argument("text", required=False)
@click.option(
    "--from",
    "source_lang",
    type=click.Choice(["en", "ne"], case_sensitive=False),
    help="Source language (auto-detected if not specified)",
)
@click.option(
    "--to",
    "target_lang",
    type=click.Choice(["en", "ne"], case_sensitive=False),
    required=True,
    help="Target language (required)",
)
@click.option(
    "--provider",
    type=click.Choice(["aws"], case_sensitive=False),
    default="aws",
    help="LLM provider to use",
)
@click.option(
    "--model",
    "model_id",
    envvar="AWS_BEDROCK_MODEL_ID",
    show_envvar=True,
    help="Model ID to use (for AWS: defaults to Claude Sonnet 4.5)",
)
@click.option(
    "--region",
    "region_name",
    envvar="AWS_REGION",
    show_envvar=True,
    help="AWS region (for AWS: defaults to us-east-1)",
)
def translate(text, source_lang, target_lang, provider, model_id, region_name):
    """Translate text between English and Nepali using AWS Bedrock.

    Supports translation from:

    - English to Nepali (Devanagari)

    - Nepali (Devanagari) to English

    - Romanized Nepali to English or Devanagari

    The source language is auto-detected if not specified.

    Configuration via environment variables:

    - AWS_REGION: AWS region (default: us-east-1)

    - AWS_BEDROCK_MODEL_ID: Model ID (default: claude-sonnet-4-5)

    - AWS_PROFILE: AWS profile name

    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY: AWS credentials

    \b
    Examples:
        nes translate --to ne "Ram Chandra Poudel"
        nes translate --to en "राम चन्द्र पौडेल"
        nes translate --to en "Ma bhat khanchu."
        nes translate --from en --to ne "Ram Chandra Poudel"
        nes translate --region us-west-2 --to ne "Hello"
        echo "Ram Chandra Poudel" | nes translate --to ne
    """
    # Normalize language codes
    if target_lang:
        target_lang = target_lang.lower()
    if source_lang:
        source_lang = source_lang.lower()

    # Validate language codes
    valid_langs = ["en", "ne"]
    if target_lang not in valid_langs:
        click.echo(
            f"Error: Invalid target language '{target_lang}'. Must be 'en' or 'ne'.",
            err=True,
        )
        raise click.Abort()
    if source_lang and source_lang not in valid_langs:
        click.echo(
            f"Error: Invalid source language '{source_lang}'. Must be 'en' or 'ne'.",
            err=True,
        )
        raise click.Abort()

    # Get translation service
    try:
        translator = get_translation_service(
            provider_name=provider, model_id=model_id, region_name=region_name
        )
    except Exception as e:
        click.echo(f"Error: Failed to initialize translation service: {e}", err=True)
        raise click.Abort()

    # Get text from argument or stdin
    if not text:
        if not sys.stdin.isatty():
            # Read from stdin
            text = sys.stdin.read().strip()
        else:
            click.echo(
                "Error: No text provided. Provide text as argument or via stdin.",
                err=True,
            )
            raise click.Abort()

    # Validate text
    if not text or not text.strip():
        click.echo("Error: Empty text provided.", err=True)
        raise click.Abort()

    # Perform translation
    try:
        result = asyncio.run(
            translator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
            )
        )

        # Display result
        _display_translation(result)

    except Exception as e:
        click.echo(f"Error: Translation failed: {e}", err=True)
        raise click.Abort()


def _display_translation(result):
    """Display translation result in human-readable format.

    Args:
        result: Translation result dictionary
    """
    # Show detected language if auto-detected
    if "detected_language" in result:
        lang_names = {"en": "English", "ne": "Nepali"}
        detected = lang_names.get(
            result["detected_language"], result["detected_language"]
        )
        click.echo(f"Detected language: {detected}")

    # Show translation
    click.echo(f"\nTranslation: {result['translated_text']}")

    # Show transliteration if available
    if "transliteration" in result and result["transliteration"]:
        click.echo(f"Transliteration: {result['transliteration']}")
