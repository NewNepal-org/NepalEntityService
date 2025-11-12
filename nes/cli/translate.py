"""Translation CLI command for Nepal Entity Service.

Provides command-line translation between English and Nepali, supporting:
- Devanagari script (native Nepali)
- Romanized Nepali text
- Automatic language detection

Environment Variables:
    NES_LLM_REGION: Region/location (AWS: us-east-1, Google: us-central1)
    NES_LLM_MODEL_ID: Model ID to use (provider-specific defaults)
    NES_PROJECT_ID: Google Cloud project ID (required for google provider)
    AWS_PROFILE: AWS profile name (automatically picked up by boto3)
    AWS_ACCESS_KEY_ID: AWS access key (automatically picked up by boto3)
    AWS_SECRET_ACCESS_KEY: AWS secret key (automatically picked up by boto3)
    AWS_SESSION_TOKEN: AWS session token (automatically picked up by boto3)
    GOOGLE_APPLICATION_CREDENTIALS: Path to Google service account key file
    OPENAI_API_KEY: OpenAI API key (required for openai provider)
    OPENAI_BASE_URL: Custom OpenAI API endpoint (optional)
"""

import asyncio
import sys

import click


def get_translation_service(provider_name, model_id=None, region_name=None, **kwargs):
    """Get or create translation service instance.

    Args:
        provider_name: Name of the LLM provider ("aws" or "google")
        model_id: Model ID to use (None to use provider default)
        region_name: Region/location (None to use provider default)
        **kwargs: Provider-specific arguments (e.g., project_id for Google)

    Returns:
        Translator instance configured with LLM provider

    Raises:
        ValueError: If an unsupported provider is specified
    """
    from nes.services.scraping import ScrapingService

    if provider_name == "aws":
        from nes.services.scraping.providers import AWSBedrockProvider

        aws_model_id = model_id or "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
        aws_region = region_name or "us-east-1"

        provider = AWSBedrockProvider(
            region_name=aws_region,
            model_id=aws_model_id,
        )
    elif provider_name == "google":
        from nes.services.scraping.providers import GoogleVertexAIProvider

        project_id = kwargs.get("project_id")
        if not project_id:
            raise ValueError(
                "Google provider requires NES_PROJECT_ID environment variable or --project-id option"
            )

        google_model_id = model_id or "gemini-2.5-pro"
        google_location = region_name or "us-central1"

        provider = GoogleVertexAIProvider(
            project_id=project_id,
            location=google_location,
            model_id=google_model_id,
        )
    elif provider_name == "openai":
        from nes.services.scraping.providers import OpenAIProvider

        openai_model_id = model_id or "gpt-4o-2024-08-06"

        provider = OpenAIProvider(
            model_id=openai_model_id,
        )
    else:
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Supported providers: 'aws', 'google', 'openai'"
        )

    service = ScrapingService(llm_provider=provider)
    return service.translator


@click.command(name="translate")
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
    type=click.Choice(["aws", "google", "openai"], case_sensitive=False),
    default="aws",
    help="LLM provider to use",
)
@click.option(
    "--model",
    "model_id",
    envvar="NES_LLM_MODEL_ID",
    show_envvar=True,
    help="Model ID to use (provider-specific defaults)",
)
@click.option(
    "--region",
    "region_name",
    envvar="NES_LLM_REGION",
    show_envvar=True,
    help="Region/location (AWS: us-east-1, Google: us-central1)",
)
@click.option(
    "--project-id",
    "project_id",
    envvar="NES_PROJECT_ID",
    show_envvar=True,
    help="Google Cloud project ID (required for google provider)",
)
def translate(
    text, source_lang, target_lang, provider, model_id, region_name, project_id
):
    """Translate text between English and Nepali using LLM providers.

    Supports translation from:

    - English to Nepali (Devanagari)

    - Nepali (Devanagari) to English

    - Romanized Nepali to English or Devanagari

    The source language is auto-detected if not specified.

    Configuration via environment variables:

    General:

    - NES_LLM_REGION: Region/location (AWS: us-east-1, Google: us-central1)

    - NES_LLM_MODEL_ID: Model ID (provider-specific defaults)

    - NES_PROJECT_ID: Google Cloud project ID (required for google)

    AWS Provider:

    - AWS_PROFILE: AWS profile name

    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY: AWS credentials

    Google Provider:

    - GOOGLE_APPLICATION_CREDENTIALS: Path to service account key

    OpenAI Provider:

    - OPENAI_API_KEY: OpenAI API key (required)

    - OPENAI_BASE_URL: Custom API endpoint (optional)

    \b
    Examples:
        nes translate --to ne "Ram Chandra Poudel"
        nes translate --to en "राम चन्द्र पौडेल"
        nes translate --provider google --to ne "Harka Sampang"
        nes translate --provider openai --to ne "Rabindra Mishra"
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
        kwargs = {}
        if provider == "google":
            kwargs["project_id"] = project_id

        translator = get_translation_service(
            provider_name=provider,
            model_id=model_id,
            region_name=region_name,
            **kwargs,
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
