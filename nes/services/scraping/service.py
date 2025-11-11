"""Scraping Service implementation for nes.

The Scraping Service provides data extraction and normalization capabilities:
- Wikipedia data extraction (English and Nepali)
- Data normalization using LLM for structured entity creation
- Relationship extraction from narrative text
- Translation between Nepali and English
- External source search capabilities

This service is standalone and does not directly access the database.
It returns normalized data for client applications to review and import.

Architecture:
    The service follows a component-based architecture with three main components:
    - WebScraper: Handles HTTP requests, rate limiting, and retry logic
    - Translator: Provides translation and transliteration capabilities
    - DataNormalizer: Extracts structured data from unstructured text

Performance Considerations:
    - Rate limiting prevents overwhelming external sources
    - Retry logic with exponential backoff handles transient failures
    - Component reuse reduces initialization overhead
    - Async operations allow concurrent processing

Error Handling:
    - Graceful degradation for missing pages or failed requests
    - Detailed error context for debugging
    - Fallback mechanisms for optional dependencies
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional, Union

from .normalization import DataNormalizer
from .providers import BaseLLMProvider, MockLLMProvider
from .translation import Translator
from .web_scraper import WebScraper

# Configure logging
logger = logging.getLogger(__name__)


class ScrapingService:
    """Scraping Service for external data extraction and normalization.

    The Scraping Service provides a pluggable architecture for extracting
    data from various external sources and normalizing it into structured
    entity and relationship data. It uses LLM providers for intelligent
    data extraction and normalization.

    Attributes:
        llm_provider: The LLM provider to use (e.g., "mock", "openai", "google")
        llm_config: Configuration for the LLM provider
        extractors: Dictionary of registered data extractors
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        web_scraper: Optional[WebScraper] = None,
        translator: Optional[Translator] = None,
        normalizer: Optional[DataNormalizer] = None,
    ):
        """Initialize the Scraping Service.

        The service requires an LLM provider instance and initializes with default
        components if not provided, allowing for dependency injection during testing
        or custom configurations.

        Args:
            llm_provider: The LLM provider instance to use (required)
                Must be an instance of BaseLLMProvider
                Examples: MockLLMProvider, AWSBedrockProvider
            web_scraper: Optional WebScraper instance (creates default if not provided)
                Allows custom rate limiting and retry configurations
            translator: Optional Translator instance (creates default if not provided)
                Allows custom translation backends
            normalizer: Optional DataNormalizer instance (creates default if not provided)
                Allows custom normalization strategies

        Examples:
            >>> # Use mock provider for testing
            >>> from nes.services.scraping.providers import MockLLMProvider
            >>> provider = MockLLMProvider()
            >>> service = ScrapingService(llm_provider=provider)

            >>> # Use AWS Bedrock provider
            >>> from nes.services.scraping.providers import AWSBedrockProvider
            >>> aws_provider = AWSBedrockProvider(region_name="us-east-1")
            >>> service = ScrapingService(llm_provider=aws_provider)

            >>> # Custom components for testing
            >>> provider = MockLLMProvider()
            >>> mock_scraper = MockWebScraper()
            >>> service = ScrapingService(
            ...     llm_provider=provider,
            ...     web_scraper=mock_scraper
            ... )
        """
        # Initialize LLM provider (required)
        self.provider = llm_provider

        # Store provider name for logging
        self.llm_provider_name = self.provider.provider_name

        # Initialize components with dependency injection support
        self.web_scraper = web_scraper or WebScraper()
        self.translator = translator or Translator(
            llm_provider=self.provider,
        )
        self.normalizer = normalizer or DataNormalizer(
            llm_provider=self.provider.provider_name,
            llm_config={},
        )

        # Initialize extractor registry
        self.extractors = self._initialize_extractors()

        logger.info(
            f"ScrapingService initialized with provider={self.llm_provider_name}, "
            f"model={self.provider.model_id}, "
            f"extractors={list(self.extractors.keys())}"
        )

    def _initialize_extractors(self) -> Dict[str, Any]:
        """Initialize pluggable data extractors.

        This method sets up the extractor architecture, allowing different
        extractors to be registered for different data sources.

        Returns:
            Dictionary of registered extractors by source name
        """
        extractors = {}

        # Register Wikipedia extractor
        extractors["wikipedia"] = self._create_wikipedia_extractor()

        # Register government site extractor (placeholder)
        extractors["government"] = self._create_government_extractor()

        # Register news extractor (placeholder)
        extractors["news"] = self._create_news_extractor()

        return extractors

    def _create_wikipedia_extractor(self) -> Dict[str, Any]:
        """Create Wikipedia data extractor.

        Returns:
            Wikipedia extractor configuration
        """
        return {
            "name": "wikipedia",
            "enabled": True,
            "base_url": "https://en.wikipedia.org/wiki/",
            "base_url_ne": "https://ne.wikipedia.org/wiki/",
        }

    def _create_government_extractor(self) -> Dict[str, Any]:
        """Create government site data extractor.

        Returns:
            Government extractor configuration
        """
        return {
            "name": "government",
            "enabled": True,
        }

    def _create_news_extractor(self) -> Dict[str, Any]:
        """Create news site data extractor.

        Returns:
            News extractor configuration
        """
        return {
            "name": "news",
            "enabled": True,
        }

    async def extract_from_wikipedia(
        self,
        page_title: str,
        language: str = "en",
    ) -> Optional[Dict[str, Any]]:
        """Extract entity data from Wikipedia.

        Extracts content from a Wikipedia page in the specified language.
        Handles disambiguation pages and missing pages gracefully with proper
        error logging and fallback mechanisms.

        Args:
            page_title: The Wikipedia page title (e.g., "Ram_Chandra_Poudel")
                Underscores are used for spaces in Wikipedia URLs
            language: Language code ("en" for English, "ne" for Nepali)
                Defaults to English if not specified

        Returns:
            Dictionary containing extracted data with keys:
                - content: The page content/text
                - url: The Wikipedia page URL
                - title: The page title
                - language: The language code
                - metadata: Additional metadata including source
            Returns None if the page doesn't exist or extraction fails

        Raises:
            No exceptions are raised; errors are logged and None is returned

        Examples:
            >>> # Extract from English Wikipedia
            >>> result = await service.extract_from_wikipedia(
            ...     page_title="Ram_Chandra_Poudel",
            ...     language="en"
            ... )
            >>> if result:
            ...     print(f"Extracted {len(result['content'])} characters")

            >>> # Extract from Nepali Wikipedia
            >>> result = await service.extract_from_wikipedia(
            ...     page_title="राम_चन्द्र_पौडेल",
            ...     language="ne"
            ... )

            >>> # Handle missing pages
            >>> result = await service.extract_from_wikipedia(
            ...     page_title="Nonexistent_Page",
            ...     language="en"
            ... )
            >>> if result is None:
            ...     print("Page not found")
        """
        try:
            logger.debug(f"Extracting Wikipedia page: {page_title} (lang={language})")

            # Use WebScraper to fetch Wikipedia page
            page_data = await self.web_scraper.fetch_wikipedia_page(
                page_title=page_title,
                language=language,
            )

            if page_data is None:
                logger.info(f"Wikipedia page not found: {page_title} (lang={language})")
                return None

            # Enrich with language and metadata
            page_data["language"] = language
            page_data["metadata"] = {
                "source": "wikipedia",
                "extractor": "wikipedia",
                "language": language,
                "page_title": page_title,
            }

            logger.debug(
                f"Successfully extracted Wikipedia page: {page_title} "
                f"({len(page_data.get('content', ''))} chars)"
            )

            return page_data

        except Exception as e:
            logger.error(
                f"Error extracting Wikipedia page {page_title} (lang={language}): {e}",
                exc_info=True,
            )
            return None

    async def normalize_person_data(
        self,
        raw_data: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:
        """Normalize person data from raw text to entity structure.

        Uses LLM-powered extraction to convert unstructured text into structured
        entity data conforming to the Person entity schema. Extracts names,
        attributes, identifiers, and other entity fields with quality assessment.

        Args:
            raw_data: Raw data dictionary containing:
                - content: The text content to normalize (required)
                - url: Source URL (optional, used for identifiers)
                - title: Source title (optional, used for name extraction)
            source: The data source identifier (e.g., "wikipedia", "government")
                Used for attribution and identifier scheme

        Returns:
            Dictionary containing normalized entity data with keys:
                - slug: Entity slug (kebab-case identifier)
                - type: Entity type ("person")
                - sub_type: Entity subtype (e.g., "politician")
                - names: List of name objects with PRIMARY/ALIAS kinds
                - identifiers: List of external identifiers
                - attributes: Dictionary of entity attributes

        Raises:
            ValueError: If raw_data is missing required fields

        Examples:
            >>> # Normalize Wikipedia data
            >>> raw_data = {
            ...     "content": "Ram Chandra Poudel is a Nepali politician.",
            ...     "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel",
            ...     "title": "Ram Chandra Poudel"
            ... }
            >>> normalized = await service.normalize_person_data(
            ...     raw_data=raw_data,
            ...     source="wikipedia"
            ... )
            >>> print(normalized["slug"])
            'ram-chandra-poudel'

            >>> # Normalize with minimal data
            >>> raw_data = {"content": "John Doe is a politician."}
            >>> normalized = await service.normalize_person_data(
            ...     raw_data=raw_data,
            ...     source="manual"
            ... )
        """
        try:
            # Validate input
            if not raw_data or "content" not in raw_data:
                raise ValueError("raw_data must contain 'content' field")

            logger.debug(f"Normalizing person data from source: {source}")

            # Use DataNormalizer component for intelligent extraction
            normalized = self.normalizer.normalize_person_data(
                raw_data=raw_data,
                source=source,
            )

            logger.debug(
                f"Successfully normalized person data: slug={normalized.get('slug')}, "
                f"names={len(normalized.get('names', []))}"
            )

            return normalized

        except Exception as e:
            logger.error(
                f"Error normalizing person data from {source}: {e}", exc_info=True
            )
            raise

    async def extract_relationships(
        self,
        text: str,
        entity_id: str,
    ) -> List[Dict[str, Any]]:
        """Extract relationships from narrative text using LLM.

        Analyzes narrative text to identify relationships between entities,
        including relationship types, target entities, and temporal information.
        Uses pattern matching and LLM-powered extraction for comprehensive
        relationship discovery.

        Args:
            text: The narrative text to analyze
                Should contain information about entity connections
            entity_id: The source entity ID for extracted relationships
                Format: "entity:type/subtype/slug"

        Returns:
            List of relationship dictionaries, each containing:
                - type: Relationship type (e.g., "MEMBER_OF", "HELD_POSITION")
                - target_entity: Information about the target entity
                    - name: Target entity name
                    - id: Target entity ID (if identifiable)
                - start_date: Optional start date (ISO format)
                - end_date: Optional end date (ISO format)
                - attributes: Additional relationship attributes
            Returns empty list if no relationships found

        Examples:
            >>> # Extract party membership
            >>> text = "Ram Chandra Poudel is a member of the Nepali Congress party."
            >>> relationships = await service.extract_relationships(
            ...     text=text,
            ...     entity_id="entity:person/ram-chandra-poudel"
            ... )
            >>> print(relationships[0]["type"])
            'MEMBER_OF'

            >>> # Extract with temporal information
            >>> text = "He served as Deputy Prime Minister from 2007 to 2009."
            >>> relationships = await service.extract_relationships(
            ...     text=text,
            ...     entity_id="entity:person/ram-chandra-poudel"
            ... )
            >>> print(relationships[0]["start_date"])
            '2007-01-01'
        """
        try:
            logger.debug(f"Extracting relationships for entity: {entity_id}")

            # Use DataNormalizer component for intelligent extraction
            relationships = self.normalizer.extract_relationships(
                text=text,
                entity_id=entity_id,
            )

            logger.debug(
                f"Extracted {len(relationships)} relationships for {entity_id}"
            )

            return relationships

        except Exception as e:
            logger.error(
                f"Error extracting relationships for {entity_id}: {e}", exc_info=True
            )
            return []

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translate text between Nepali and English.

        Translates text from source language to target language with automatic
        language detection if source is not specified. Includes transliteration
        for proper nouns and names.

        Args:
            text: The text to translate
                Can be in Nepali (Devanagari) or English (Latin)
            target_lang: Target language code ("en" or "ne")
                "en" for English, "ne" for Nepali
            source_lang: Source language code (optional, auto-detected if not provided)
                If None, language is detected from character ranges

        Returns:
            Dictionary containing:
                - translated_text: The translated text
                - detected_language: The detected source language (if auto-detected)
                - source_language: The source language used
                - target_language: The target language
                - transliteration: Transliterated version (if applicable)
                    Provided for Devanagari ↔ Roman conversions

        Raises:
            ValueError: If target_lang is not "en" or "ne"

        Examples:
            >>> # Translate Nepali to English with explicit source
            >>> result = await service.translate(
            ...     text="राम चन्द्र पौडेल",
            ...     source_lang="ne",
            ...     target_lang="en"
            ... )
            >>> print(result["translated_text"])
            'Ram Chandra Poudel'

            >>> # Auto-detect source language
            >>> result = await service.translate(
            ...     text="राम चन्द्र पौडेल",
            ...     target_lang="en"
            ... )
            >>> print(result["detected_language"])
            'ne'

            >>> # Translate English to Nepali
            >>> result = await service.translate(
            ...     text="Ram Chandra Poudel",
            ...     source_lang="en",
            ...     target_lang="ne"
            ... )
            >>> print(result["transliteration"])
            'raam chandra poudel'
        """
        try:
            # Validate target language
            if target_lang not in ("en", "ne"):
                raise ValueError(
                    f"Invalid target_lang: {target_lang}. Must be 'en' or 'ne'"
                )

            logger.debug(
                f"Translating text (len={len(text)}) from {source_lang or 'auto'} to {target_lang}"
            )

            # Use the Translator component
            result = await self.translator.translate(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
            )

            logger.debug(
                f"Translation complete: {result.get('source_language')} → {target_lang}"
            )

            return result

        except Exception as e:
            logger.error(f"Error translating text: {e}", exc_info=True)
            raise

    async def search_external_sources(
        self,
        query: str,
        sources: List[str],
    ) -> List[Dict[str, Any]]:
        """Search external sources for entity information.

        Searches multiple external sources (Wikipedia, government sites, news)
        for information about entities matching the query. Results are aggregated
        from all enabled sources with proper error handling per source.

        Args:
            query: The search query
                Can be entity name, keyword, or phrase
            sources: List of source names to search
                Supported: ["wikipedia", "government", "news"]
                Only enabled extractors will be queried

        Returns:
            List of search result dictionaries, each containing:
                - source: The source name
                - title: Result title
                - url: Result URL
                - summary: Brief summary or snippet (key may vary by source)
            Returns empty list if no results found or all sources fail

        Examples:
            >>> # Search Wikipedia only
            >>> results = await service.search_external_sources(
            ...     query="Ram Chandra Poudel",
            ...     sources=["wikipedia"]
            ... )
            >>> for result in results:
            ...     print(f"{result['source']}: {result['title']}")

            >>> # Search multiple sources
            >>> results = await service.search_external_sources(
            ...     query="Ram Chandra Poudel",
            ...     sources=["wikipedia", "government", "news"]
            ... )
            >>> print(f"Found {len(results)} results across all sources")

            >>> # Handle no results gracefully
            >>> results = await service.search_external_sources(
            ...     query="NonexistentPerson12345",
            ...     sources=["wikipedia"]
            ... )
            >>> if not results:
            ...     print("No results found")
        """
        results = []

        logger.debug(f"Searching external sources: query='{query}', sources={sources}")

        for source in sources:
            try:
                # Check if extractor exists and is enabled
                if source not in self.extractors:
                    logger.warning(f"Unknown source: {source}")
                    continue

                extractor = self.extractors[source]
                if not extractor.get("enabled", False):
                    logger.debug(f"Source disabled: {source}")
                    continue

                # Search based on source type
                source_results = await self._search_source(source, query)
                results.extend(source_results)

                logger.debug(f"Found {len(source_results)} results from {source}")

            except Exception as e:
                # Log error but continue with other sources
                logger.error(f"Error searching {source}: {e}", exc_info=True)
                continue

        logger.debug(f"Total results found: {len(results)}")
        return results

    async def _search_source(
        self,
        source: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Search a specific source for results.

        Internal method to handle source-specific search logic.

        Args:
            source: The source name
            query: The search query

        Returns:
            List of search results from the source
        """
        if source == "wikipedia":
            return await self._search_wikipedia(query)
        elif source == "government":
            return await self._search_government(query)
        elif source == "news":
            return await self._search_news(query)
        else:
            return []

    async def _search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        """Search Wikipedia for results."""
        wiki_results = await self.web_scraper.search_wikipedia(
            query=query,
            language="en",
            max_results=5,
        )

        return [
            {
                "source": "wikipedia",
                "title": result["title"],
                "url": result["url"],
                "summary": result["summary"],
            }
            for result in wiki_results
        ]

    async def _search_government(self, query: str) -> List[Dict[str, Any]]:
        """Search government sources for results.

        TODO: Implement actual government API integration.
        """
        logger.warning("Government search not yet implemented")
        return []

    async def _search_news(self, query: str) -> List[Dict[str, Any]]:
        """Search news sources for results.

        TODO: Implement actual news API integration.
        """
        logger.warning("News search not yet implemented")
        return []
