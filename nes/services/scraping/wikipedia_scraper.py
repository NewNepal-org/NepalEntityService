"""Wikipedia Scraper for extracting raw data from Wikipedia pages.

This module provides a simple interface for scraping Wikipedia pages,
specifically designed for extracting politician and person data. It returns
raw, unnormalized data that can be processed and normalized later.

Key Features:
    - Simple interface: scrape_politician(name) method
    - Extracts comprehensive raw data from Wikipedia
    - Supports both English and Nepali Wikipedia
    - Handles disambiguation pages
    - Returns structured raw data for later normalization
"""

import logging
from typing import Any, Dict, List, Optional

from .web_scraper import WebScraper

# Configure logging
logger = logging.getLogger(__name__)


class WikipediaScraper:
    """Simple Wikipedia scraper for extracting raw politician data.

    Provides a straightforward interface for scraping Wikipedia pages
    and extracting comprehensive raw data that can be normalized later.

    Attributes:
        web_scraper: Internal WebScraper instance for HTTP operations
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        requests_per_minute: int = 30,
        max_retries: int = 3,
    ):
        """Initialize the Wikipedia scraper.

        Args:
            requests_per_second: Maximum requests per second per domain
            requests_per_minute: Maximum requests per minute per domain
            max_retries: Maximum number of retry attempts
        """
        self.web_scraper = WebScraper(
            requests_per_second=requests_per_second,
            requests_per_minute=requests_per_minute,
            max_retries=max_retries,
        )

    async def scrape_politician(
        self, name: str, languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Scrape Wikipedia data for a politician or person.

        Searches Wikipedia for the given name and extracts comprehensive
        raw data from the page(s). Attempts to fetch both English and
        Nepali versions if available.

        Args:
            name: The person's name (e.g., "Ram Chandra Poudel")
            languages: List of language codes to fetch (default: ["en", "ne"])
                Supported: "en" (English), "ne" (Nepali)

        Returns:
            Dictionary containing raw scraped data with keys:
                - name: The original search name
                - pages: Dictionary of language -> page data
                    Each page data contains:
                    - title: Page title
                    - url: Page URL
                    - content: Full page content
                    - summary: Page summary
                    - categories: List of categories
                    - links: List of linked pages
                    - images: List of image URLs
                    - infobox: Infobox data (if available)
                    - sections: Page sections (if available)
                    - references: References (if available)
                - metadata: Additional metadata
                    - found_languages: List of languages where page was found
                    - search_results: Search results if exact match not found
                    - disambiguation: Whether disambiguation page was encountered

        Examples:
            >>> scraper = WikipediaScraper()
            >>> raw_data = await scraper.scrape_politician("Ram Chandra Poudel")
            >>> print(raw_data["pages"]["en"]["title"])
            'Ram Chandra Poudel'

            >>> # Fetch only English version
            >>> raw_data = await scraper.scrape_politician(
            ...     "Ram Chandra Poudel",
            ...     languages=["en"]
            ... )
        """
        if languages is None:
            languages = ["en", "ne"]

        logger.info(f"Scraping Wikipedia for: {name} (languages: {languages})")

        result: Dict[str, Any] = {
            "name": name,
            "pages": {},
            "metadata": {
                "found_languages": [],
                "search_results": [],
                "disambiguation": False,
            },
        }

        # Try to fetch pages in each language
        for lang in languages:
            try:
                page_data = await self._fetch_page_for_name(name, lang)
                if page_data:
                    result["pages"][lang] = page_data
                    result["metadata"]["found_languages"].append(lang)

                    # Check for disambiguation
                    if page_data.get("disambiguation"):
                        result["metadata"]["disambiguation"] = True

            except Exception as e:
                logger.warning(f"Failed to fetch {lang} Wikipedia page for {name}: {e}")
                continue

        # If no pages found, try searching
        if not result["pages"]:
            logger.info(f"No exact match found for {name}, searching...")
            search_results = await self.web_scraper.search_wikipedia(
                query=name, language="en", max_results=5
            )
            result["metadata"]["search_results"] = search_results

        logger.info(
            f"Scraped {len(result['pages'])} page(s) for {name} "
            f"(found in: {result['metadata']['found_languages']})"
        )

        return result

    async def _fetch_page_for_name(
        self, name: str, language: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch Wikipedia page for a given name in specified language.

        First tries the exact name, then searches if not found.

        Args:
            name: The person's name
            language: Language code ("en" or "ne")

        Returns:
            Dictionary with page data or None if not found
        """
        # Convert name to Wikipedia page title format (spaces to underscores)
        # Wikipedia page titles are case-sensitive and use underscores
        page_title = name.strip().replace(" ", "_")

        # Try fetching with exact title
        page_data = await self.web_scraper.fetch_wikipedia_page(
            page_title=page_title, language=language
        )

        if page_data:
            # Enrich with additional data
            enriched_data = self._enrich_page_data(page_data, language)
            return enriched_data

        # If not found, try searching
        logger.debug(f"Exact match not found for {page_title}, searching...")
        search_results = await self.web_scraper.search_wikipedia(
            query=name, language=language, max_results=1
        )

        if search_results:
            # Try first search result
            first_result_title = search_results[0]["title"]
            page_data = await self.web_scraper.fetch_wikipedia_page(
                page_title=first_result_title, language=language
            )

            if page_data:
                enriched_data = self._enrich_page_data(page_data, language)
                enriched_data["matched_via_search"] = True
                enriched_data["original_search"] = name
                return enriched_data

        return None

    def _enrich_page_data(
        self, page_data: Dict[str, Any], language: str
    ) -> Dict[str, Any]:
        """Enrich page data with additional information.

        Extracts infobox data, sections, and other structured information
        from the Wikipedia page content.

        Args:
            page_data: Basic page data from WebScraper
            language: Language code

        Returns:
            Enriched page data dictionary
        """
        enriched = page_data.copy()

        # Try to extract infobox data from content
        content = page_data.get("content", "")
        infobox = self._extract_infobox(content)
        if infobox:
            enriched["infobox"] = infobox

        # Extract sections from content
        sections = self._extract_sections(content)
        if sections:
            enriched["sections"] = sections

        # Extract basic metadata
        enriched["language"] = language
        enriched["content_length"] = len(content)
        enriched["link_count"] = len(page_data.get("links", []))
        enriched["image_count"] = len(page_data.get("images", []))

        return enriched

    def _extract_infobox(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract infobox data from Wikipedia content.

        Attempts to parse infobox-style information from the content.
        This is a basic extraction - more sophisticated parsing could
        be added later.

        Args:
            content: Wikipedia page content

        Returns:
            Dictionary with infobox data or None
        """
        infobox: Dict[str, Any] = {}

        # Look for common infobox patterns in the first few paragraphs
        lines = content.split("\n")[:50]  # First 50 lines

        for line in lines:
            line = line.strip()

            # Look for key-value patterns (basic extraction)
            if ":" in line and len(line) < 200:  # Likely infobox line
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    # Skip if it looks like regular text
                    if len(key) < 50 and len(value) < 200:
                        # Clean up common Wikipedia formatting
                        value = value.replace("[[", "").replace("]]", "")
                        value = value.split("|")[0]  # Handle piped links

                        if key and value:
                            infobox[key.lower().replace(" ", "_")] = value

        return infobox if infobox else None

    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract section headings and content from Wikipedia page.

        Args:
            content: Wikipedia page content

        Returns:
            List of section dictionaries with 'heading' and 'content'
        """
        sections: List[Dict[str, Any]] = []
        lines = content.split("\n")

        current_section: Optional[Dict[str, Any]] = None
        current_content: List[str] = []

        for line in lines:
            line_stripped = line.strip()

            # Check if line is a section heading (starts with ==)
            if line_stripped.startswith("==") and line_stripped.endswith("=="):
                # Save previous section
                if current_section:
                    current_section["content"] = "\n".join(current_content).strip()
                    sections.append(current_section)

                # Start new section
                heading = line_stripped.strip("=").strip()
                current_section = {"heading": heading, "content": ""}
                current_content = []
            elif current_section:
                current_content.append(line)
            elif not current_section:
                # Content before first section
                if line_stripped:
                    current_content.append(line)

        # Save last section
        if current_section:
            current_section["content"] = "\n".join(current_content).strip()
            sections.append(current_section)

        return sections
