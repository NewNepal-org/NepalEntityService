"""
Script to generate parties-data-en.json by translating Nepali party data to English.

This script reads the raw CSV data and uses Google Vertex AI to translate
party information from Nepali to English using structured data extraction.
"""

import asyncio
import csv
import json
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from nes.services.scraping.providers.google import GoogleVertexAIProvider


class PoliticalParty(BaseModel):
    """Pydantic model for political party translation."""

    name: str = Field(description="Name of the political party in English")
    address: str = Field(description="Address of the party headquarters in English")
    contact: List[str] = Field(description="List of contact phone numbers")
    main_person: str = Field(
        description="Name and title of the main person/leader in English"
    )
    symbol_name: str = Field("", description="Symbol name of the party in English")


INSTRUCTIONS = """
You are a translation system converting Nepali political party information to English.
Translate the party name, address, main person name/title, and symbol name to English.
If a field is empty, use an empty string or empty list.
"""


async def translate_party(provider: GoogleVertexAIProvider, party_data: dict) -> dict:
    """Translate a single party's data from Nepali to English."""
    # Create input model
    party = PoliticalParty(
        name=party_data["दलको नाम"],
        address=party_data["दलको मुख्य कार्यालय (ठेगाना)"],
        contact=(
            party_data["सम्पर्क टेलिफोन/मोबाइल"].split(", ")
            if party_data["सम्पर्क टेलिफोन/मोबाइल"]
            else []
        ),
        main_person=party_data["प्रमुख पदाधिकारीको नाम"],
        symbol_name=party_data["चिन्हको नाम"] if party_data["चिन्हको नाम"] else "",
    )

    # Extract structured translation
    result = await provider.extract_structured_data(
        f"Translate this: {party.model_dump()}",
        PoliticalParty.model_json_schema(),
        instructions=INSTRUCTIONS,
    )

    return result


async def main():
    """Main function to generate translations."""
    # Load environment variables
    load_dotenv()

    # Get script directory
    script_dir = Path(__file__).parent
    source_dir = script_dir / "source"

    # Initialize AI provider
    project_id = os.environ.get("NES_PROJECT_ID")
    if not project_id:
        raise ValueError("NES_PROJECT_ID environment variable not set")

    provider = GoogleVertexAIProvider(
        project_id=project_id,
        model_id="gemini-2.5-pro",
        temperature=0.3,
    )

    print("Loading raw party data...")

    # Read raw CSV
    raw_data = []
    with open(source_dir / "parties-2082.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        raw_data = list(reader)

    print(f"Found {len(raw_data)} parties to translate")

    # Load existing translations if any
    output_file = source_dir / "parties-data-en.json"
    translations = {}
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
        print(f"Loaded {len(translations)} existing translations")

    # Translate each party
    for i, row in enumerate(raw_data, 1):
        party_name_ne = row["दलको नाम"]

        if party_name_ne in translations:
            print(
                f"[{i}/{len(raw_data)}] Skipping (already translated): {party_name_ne}"
            )
            continue

        print(f"[{i}/{len(raw_data)}] Translating: {party_name_ne}")
        translated = await translate_party(provider, row)
        translations[party_name_ne] = translated
        print(f"  ✓ {translated.get('name', 'N/A')}")

        # Save after each translation
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Completed: {len(translations)} translations in {output_file}")

    # Print token usage
    usage = provider.get_token_usage()
    print(f"\nToken usage:")
    print(f"  Input:  {usage['input_tokens']:,}")
    print(f"  Output: {usage['output_tokens']:,}")
    print(f"  Total:  {usage['total_tokens']:,}")


if __name__ == "__main__":
    asyncio.run(main())
