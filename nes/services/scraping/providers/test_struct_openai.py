# Ensure project root is in sys.path for direct execution
# smoke_test_openai_structured.py
import asyncio
import os
import sys

from nes.services.scraping.providers.openai import OpenAIProvider


async def main():
    provider = OpenAIProvider()  # reads API key, base URL, model from .env

    # --- Test structured extraction ---
    text_to_analyze = "John Doe is 32 years old and lives in Kathmandu."
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "city": {"type": "string"},
        },
        "required": ["name", "age", "city"],
    }
    instructions = "Extract name, age, and city from the text and return as JSON."

    print("Running structured extraction...")
    result = await provider.extract_structured_data(
        text=text_to_analyze, schema=schema, instructions=instructions
    )
    print("Structured extraction result:", result)

    # --- Optional: Test simple text generation ---
    print("\nRunning simple text generation...")
    response = await provider.generate_text(
        "Write a one-sentence description of Kathmandu."
    )
    print("Text generation result:", response)


if __name__ == "__main__":
    asyncio.run(main())
