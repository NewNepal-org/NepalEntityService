"""Example: Scrape Wikipedia data for a politician.

This example demonstrates how to:
1. Use WikipediaScraper to extract raw data from Wikipedia
2. View the scraped data structure
3. Save the raw data for later normalization

The example uses authentic Nepali politician data.
"""

import asyncio
import json
from pathlib import Path

from nes.services.scraping import WikipediaScraper


async def main():
    """Scrape Wikipedia data for a politician."""

    # Define the person's name to search (change this to scrape different people)
    search_name = "KP Oli"

    print("=" * 70)
    print(f"Wikipedia Scraper Example - {search_name}")
    print("=" * 70)

    # Initialize the scraper
    print("\n1. Initializing WikipediaScraper...")
    scraper = WikipediaScraper()
    print("   ✓ Scraper initialized")

    # Scrape data for a politician
    print(f"\n2. Scraping Wikipedia for: {search_name}")
    print("   (This may take a few seconds...)")

    try:
        raw_data = await scraper.scrape_politician(search_name)
    except Exception as e:
        print(f"   ❌ Error scraping: {e}")
        print("\n   Make sure you have installed scraping dependencies:")
        print("   poetry install --extras scraping")
        return

    # Print summary
    print(f"\n3. Scraping Results:")
    print(f"   ✓ Scraped data for: {raw_data['name']}")
    print(f"   ✓ Found in languages: {raw_data['metadata']['found_languages']}")
    print(f"   ✓ Number of pages: {len(raw_data['pages'])}")

    # Show details for each language
    for lang, page_data in raw_data["pages"].items():
        print(f"\n   {lang.upper()} Wikipedia Page:")
        print(f"     Title: {page_data.get('title')}")
        print(f"     URL: {page_data.get('url')}")
        print(f"     Content length: {page_data.get('content_length', 0):,} characters")

        summary = page_data.get("summary", "")
        if summary:
            print(f"     Summary: {summary[:150]}...")

        print(f"     Categories: {len(page_data.get('categories', []))}")
        print(f"     Links: {page_data.get('link_count', 0)}")
        print(f"     Images: {page_data.get('image_count', 0)}")

        if page_data.get("infobox"):
            infobox_fields = list(page_data.get("infobox", {}).keys())
            print(f"     Infobox fields: {len(infobox_fields)}")
            print(f"       Sample fields: {', '.join(infobox_fields[:5])}")

        if page_data.get("sections"):
            sections = page_data.get("sections", [])
            print(f"     Sections: {len(sections)}")
            print(
                f"       Section headings: {', '.join([s.get('heading', '') for s in sections[:5]])}"
            )

    # Check for disambiguation
    if raw_data["metadata"].get("disambiguation"):
        print("\n   ⚠ Note: Disambiguation page encountered")

    # Check for search results if no exact match
    if raw_data["metadata"].get("search_results"):
        print(f"\n   Search results (if exact match not found):")
        for result in raw_data["metadata"]["search_results"][:3]:
            print(f"     - {result.get('title')}")

    # Update the name in raw_data to use the Wikipedia page title
    # Prefer English title, fallback to Nepali, or keep original if neither found
    if raw_data["pages"]:
        if "en" in raw_data["pages"]:
            wikipedia_name = raw_data["pages"]["en"].get("title", raw_data["name"])
        elif "ne" in raw_data["pages"]:
            wikipedia_name = raw_data["pages"]["ne"].get("title", raw_data["name"])
        else:
            # Use first available page title
            first_lang = list(raw_data["pages"].keys())[0]
            wikipedia_name = raw_data["pages"][first_lang].get(
                "title", raw_data["name"]
            )

        # Update the name in the data to use Wikipedia's canonical name
        raw_data["name"] = wikipedia_name
        print(f"\n   Using Wikipedia name: {wikipedia_name}")

    # Save to file
    print("\n4. Saving raw data to file...")
    output_dir = Path("examples")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{search_name}_scraped_wikipedia_data.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    print(f"   ✓ Saved full data to: {output_file}")
    print(f"   File size: {output_file.stat().st_size:,} bytes")

    # Show next steps
    print("\n5. Next Steps:")
    print("   You can now normalize this raw data using DataNormalizer:")
    print("   ```python")
    print("   from nes.services.scraping import DataNormalizer")
    print("   normalizer = DataNormalizer()")
    print("   entity_data = await normalizer.normalize(raw_data)")
    print("   ```")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
