# smoke_test_anthropic_structured.py
# Real-world Anthropic provider test: structured extraction + translation

import asyncio
import os
import sys

from nes.services.scraping.providers.anthropic import AnthropicProvider


async def main():
    """
    This script performs two live tests:
      1. Structured data extraction using Claude.
      2. Simple text translation between Nepali and English.
    """

    provider = AnthropicProvider()  # reads API key, base URL, model from .env

    # --- 1. Test structured extraction ---
    text_to_analyze = "Sita is 28 years old and lives in Pokhara."
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "city": {"type": "string"},
        },
        "required": ["name", "age", "city"],
    }
    instructions = (
        "Extract the person's name, age, and city from the text and return JSON."
    )

    print("🔍 Running structured extraction...")
    structured_result = await provider.extract_structured_data(
        text=text_to_analyze,
        schema=schema,
        instructions=instructions,
    )
    print("✅ Structured extraction result:", structured_result)

    # --- 2. Test translation (Nepali → English and English → Nepali) ---
    print("\n🌐 Running translation tests...")

    # --- 3. Simple text generation ---
    print("\n✍️ Running simple text generation...")
    gen_text = await provider.generate_text("Describe Pokhara in one sentence.")
    print("Generated text:", gen_text)

    text_ne = "राम काठमाडौंमा बस्छ।"
    translated_en = await provider.translate(
        text=text_ne, source_lang="ne", target_lang="en"
    )
    print("Nepali → English:", translated_en)

    text_en = "Sita lives in Pokhara."
    translated_ne = await provider.translate(
        text=text_en, source_lang="en", target_lang="ne"
    )
    print("English → Nepali:", translated_ne)

    # --- Token usage summary ---
    print("\n📊 Token usage summary:", provider.get_token_usage())


if __name__ == "__main__":
    asyncio.run(main())
