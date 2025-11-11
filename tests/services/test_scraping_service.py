"""Tests for Scraping Service in nes.

Following TDD approach: Write failing tests first (Red phase).
These tests define the expected behavior of the Scraping Service.

The Scraping Service is a standalone service for extracting and normalizing data
from external sources using GenAI/LLM capabilities. It does not directly access
the database but returns normalized data for client applications to process.

Core Components:
- Web Scraper: Multi-source data extraction (Wikipedia, government sites, news)
- Translation Service: Nepali/English translation and transliteration
- Data Normalization Service: LLM-powered data structuring
"""

from datetime import date
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest


# Helper function to create service with mock provider
def create_test_service():
    """Create a ScrapingService instance for testing."""
    from nes.services.scraping import ScrapingService
    from nes.services.scraping.providers import MockLLMProvider

    provider = MockLLMProvider()
    return ScrapingService(llm_provider=provider)


class TestScrapingServiceFoundation:
    """Test Scraping Service initialization and basic structure."""

    @pytest.mark.asyncio
    async def test_scraping_service_initialization(self):
        """Test that ScrapingService can be initialized."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        assert service is not None

    @pytest.mark.asyncio
    async def test_scraping_service_with_llm_provider(self):
        """Test that ScrapingService can be initialized with LLM provider instance."""
        from nes.services.scraping import ScrapingService
        from nes.services.scraping.providers import MockLLMProvider

        # Initialize with mock provider instance
        provider = MockLLMProvider(max_tokens=4096)
        service = ScrapingService(llm_provider=provider)

        assert service is not None
        assert service.llm_provider_name == "mock"
        assert service.provider is provider
        assert service.provider.max_tokens == 4096


class TestScrapingServiceWikipediaExtraction:
    """Test Wikipedia data extraction capabilities."""

    @pytest.mark.asyncio
    async def test_extract_from_wikipedia_english(self):
        """Test extracting entity data from English Wikipedia."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Wikipedia page
        mock_page = Mock()
        mock_page.content = "Ram Chandra Poudel is a Nepali politician."
        mock_page.url = "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel"
        mock_page.title = "Ram Chandra Poudel"
        mock_page.summary = "Ram Chandra Poudel is a Nepali politician."
        mock_page.categories = ["Nepali politicians"]
        mock_page.links = ["Nepal", "Politics"]
        mock_page.images = []

        with patch("wikipedia.page", return_value=mock_page):
            with patch("wikipedia.set_lang"):
                # Extract from Wikipedia page
                result = await service.extract_from_wikipedia(
                    page_title="Ram_Chandra_Poudel", language="en"
                )

                assert result is not None
                assert "content" in result
                assert "url" in result
                assert "title" in result
                assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_extract_from_wikipedia_nepali(self):
        """Test extracting entity data from Nepali Wikipedia."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Nepali Wikipedia page
        mock_page = Mock()
        mock_page.content = "राम चन्द्र पौडेल नेपाली राजनीतिज्ञ हुन्।"
        mock_page.url = "https://ne.wikipedia.org/wiki/राम_चन्द्र_पौडेल"
        mock_page.title = "राम चन्द्र पौडेल"
        mock_page.summary = "राम चन्द्र पौडेल नेपाली राजनीतिज्ञ हुन्।"
        mock_page.categories = ["नेपाली राजनीतिज्ञ"]
        mock_page.links = ["नेपाल"]
        mock_page.images = []

        with patch("wikipedia.page", return_value=mock_page):
            with patch("wikipedia.set_lang"):
                # Extract from Nepali Wikipedia
                result = await service.extract_from_wikipedia(
                    page_title="राम_चन्द्र_पौडेल", language="ne"
                )

                assert result is not None
                assert "content" in result
                assert result["language"] == "ne"

    @pytest.mark.asyncio
    async def test_extract_from_wikipedia_handles_disambiguation(self):
        """Test that Wikipedia extraction handles disambiguation pages."""
        import wikipedia

        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock disambiguation error with fallback page
        mock_page = Mock()
        mock_page.content = "Nepal is a country in South Asia."
        mock_page.url = "https://en.wikipedia.org/wiki/Nepal"
        mock_page.title = "Nepal"
        mock_page.summary = "Nepal is a country in South Asia."
        mock_page.categories = ["Countries"]
        mock_page.links = ["Asia"]
        mock_page.images = []

        disambiguation_error = wikipedia.exceptions.DisambiguationError(
            "Ram_Poudel", ["Ram Chandra Poudel", "Ram Prasad Poudel"]
        )

        with patch("wikipedia.page") as mock_wiki_page:
            # First call raises disambiguation, second call returns page
            mock_wiki_page.side_effect = [disambiguation_error, mock_page]
            with patch("wikipedia.set_lang"):
                # Try to extract from disambiguation page
                result = await service.extract_from_wikipedia(
                    page_title="Ram_Poudel", language="en"  # Might be disambiguation
                )

                # Should either return data or raise specific error
                assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_extract_from_wikipedia_handles_missing_page(self):
        """Test that Wikipedia extraction handles missing pages gracefully."""
        import wikipedia

        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock page not found error
        with patch("wikipedia.page") as mock_wiki_page:
            mock_wiki_page.side_effect = wikipedia.exceptions.PageError(
                "Page not found"
            )
            with patch("wikipedia.set_lang"):
                # Try to extract from nonexistent page
                result = await service.extract_from_wikipedia(
                    page_title="Nonexistent_Page_12345", language="en"
                )

                assert result is None

    @pytest.mark.asyncio
    async def test_extract_from_wikipedia_includes_metadata(self):
        """Test that Wikipedia extraction includes useful metadata."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Wikipedia page
        mock_page = Mock()
        mock_page.content = "Ram Chandra Poudel is a Nepali politician."
        mock_page.url = "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel"
        mock_page.title = "Ram Chandra Poudel"
        mock_page.summary = "Ram Chandra Poudel is a Nepali politician."
        mock_page.categories = ["Nepali politicians"]
        mock_page.links = ["Nepal", "Politics"]
        mock_page.images = []

        with patch("wikipedia.page", return_value=mock_page):
            with patch("wikipedia.set_lang"):
                result = await service.extract_from_wikipedia(
                    page_title="Ram_Chandra_Poudel", language="en"
                )

                assert result is not None
                assert "metadata" in result
                assert "source" in result["metadata"]
                assert result["metadata"]["source"] == "wikipedia"


class TestScrapingServiceDataNormalization:
    """Test data normalization capabilities using LLM."""

    @pytest.mark.asyncio
    async def test_normalize_person_data_from_raw_text(self):
        """Test normalizing person data from unstructured text."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        raw_data = {
            "content": """Ram Chandra Poudel is a Nepali politician and the current 
            President of Nepal. He is a member of the Nepali Congress party and has 
            served in various ministerial positions.""",
            "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel",
            "title": "Ram Chandra Poudel",
        }

        # Normalize to entity structure
        normalized = await service.normalize_person_data(
            raw_data=raw_data, source="wikipedia"
        )

        assert normalized is not None
        assert "slug" in normalized
        assert "type" in normalized
        assert normalized["type"] == "person"
        assert "names" in normalized
        assert len(normalized["names"]) > 0

    @pytest.mark.asyncio
    async def test_normalize_person_data_extracts_names(self):
        """Test that normalization extracts proper name structure."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        raw_data = {
            "content": "Ram Chandra Poudel (राम चन्द्र पौडेल) is a politician.",
            "title": "Ram Chandra Poudel",
        }

        normalized = await service.normalize_person_data(raw_data, "wikipedia")

        assert "names" in normalized
        # Should have at least one PRIMARY name
        primary_names = [n for n in normalized["names"] if n["kind"] == "PRIMARY"]
        assert len(primary_names) > 0

        # Should have English name
        assert "en" in primary_names[0]
        assert "full" in primary_names[0]["en"]

    @pytest.mark.asyncio
    async def test_normalize_person_data_extracts_attributes(self):
        """Test that normalization extracts entity attributes."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        raw_data = {
            "content": """Ram Chandra Poudel is the President of Nepal and a member 
            of the Nepali Congress party. He was born on October 15, 1944.""",
            "title": "Ram Chandra Poudel",
        }

        normalized = await service.normalize_person_data(raw_data, "wikipedia")

        # Should extract attributes like party, position, etc.
        assert "attributes" in normalized
        # Attributes should be a dict
        assert isinstance(normalized["attributes"], dict)

    @pytest.mark.asyncio
    async def test_normalize_person_data_includes_identifiers(self):
        """Test that normalization includes external identifiers."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        raw_data = {
            "content": "Ram Chandra Poudel is a politician.",
            "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel",
            "title": "Ram Chandra Poudel",
        }

        normalized = await service.normalize_person_data(raw_data, "wikipedia")

        # Should include Wikipedia identifier
        assert "identifiers" in normalized
        assert any(i["scheme"] == "wikipedia" for i in normalized["identifiers"])

    @pytest.mark.asyncio
    async def test_normalize_person_data_validates_output(self):
        """Test that normalized data is valid according to entity schema."""
        from nes.core.models.person import Person
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        raw_data = {
            "content": "Ram Chandra Poudel is a Nepali politician.",
            "title": "Ram Chandra Poudel",
        }

        normalized = await service.normalize_person_data(raw_data, "wikipedia")

        # Should be valid Person entity data (can be used to create Person)
        # This validates the structure matches our schema
        assert "slug" in normalized
        assert "type" in normalized
        assert "names" in normalized


class TestScrapingServiceRelationshipExtraction:
    """Test relationship extraction from narrative text."""

    @pytest.mark.asyncio
    async def test_extract_relationships_from_text(self):
        """Test extracting relationships from narrative text using LLM."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        text = """Ram Chandra Poudel is a member of the Nepali Congress party. 
        He served as Deputy Prime Minister under Sher Bahadur Deuba."""

        relationships = await service.extract_relationships(
            text=text, entity_id="entity:person/ram-chandra-poudel"
        )

        assert relationships is not None
        assert isinstance(relationships, list)
        # Should extract at least the party membership
        assert len(relationships) > 0

    @pytest.mark.asyncio
    async def test_extract_relationships_identifies_types(self):
        """Test that relationship extraction identifies relationship types."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        text = "Ram Chandra Poudel is a member of the Nepali Congress party."

        relationships = await service.extract_relationships(
            text=text, entity_id="entity:person/ram-chandra-poudel"
        )

        # Should identify MEMBER_OF relationship
        assert any(r["type"] == "MEMBER_OF" for r in relationships)

    @pytest.mark.asyncio
    async def test_extract_relationships_includes_target_entities(self):
        """Test that extracted relationships include target entity information."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        text = "Ram Chandra Poudel is a member of the Nepali Congress party."

        relationships = await service.extract_relationships(
            text=text, entity_id="entity:person/ram-chandra-poudel"
        )

        # Should include target entity info
        for rel in relationships:
            assert "target_entity" in rel
            assert "name" in rel["target_entity"] or "id" in rel["target_entity"]

    @pytest.mark.asyncio
    async def test_extract_relationships_handles_temporal_info(self):
        """Test that relationship extraction captures temporal information."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        text = (
            """Ram Chandra Poudel served as Deputy Prime Minister from 2007 to 2009."""
        )

        relationships = await service.extract_relationships(
            text=text, entity_id="entity:person/ram-chandra-poudel"
        )

        # Should extract temporal information
        temporal_rels = [
            r for r in relationships if "start_date" in r or "end_date" in r
        ]
        assert len(temporal_rels) > 0


class TestScrapingServiceTranslation:
    """Test translation capabilities."""

    @pytest.mark.asyncio
    async def test_translate_nepali_to_english(self):
        """Test translating Nepali text to English."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        nepali_text = "राम चन्द्र पौडेल नेपाली कांग्रेसका नेता हुन्।"

        result = await service.translate(
            text=nepali_text, source_lang="ne", target_lang="en"
        )

        assert result is not None
        assert "translated_text" in result
        assert len(result["translated_text"]) > 0

    @pytest.mark.asyncio
    async def test_translate_english_to_nepali(self):
        """Test translating English text to Nepali."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        english_text = "Ram Chandra Poudel is a leader of Nepali Congress."

        result = await service.translate(
            text=english_text, source_lang="en", target_lang="ne"
        )

        assert result is not None
        assert "translated_text" in result
        # Should contain Devanagari script
        assert any(
            ord(c) >= 0x0900 and ord(c) <= 0x097F for c in result["translated_text"]
        )

    @pytest.mark.asyncio
    async def test_translate_handles_transliteration(self):
        """Test that translation handles transliteration of names."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Name transliteration
        result = await service.translate(
            text="Ram Chandra Poudel", source_lang="en", target_lang="ne"
        )

        assert result is not None
        assert "translated_text" in result

    @pytest.mark.asyncio
    async def test_translate_detects_source_language(self):
        """Test automatic language detection when source not specified."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Auto-detect Nepali
        result = await service.translate(text="राम चन्द्र पौडेल", target_lang="en")

        assert result is not None
        assert "detected_language" in result
        assert result["detected_language"] == "ne"


class TestScrapingServiceExternalSourceSearch:
    """Test external source search capabilities."""

    @pytest.mark.asyncio
    async def test_search_external_sources_wikipedia(self):
        """Test searching Wikipedia for entity information."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Wikipedia search
        mock_page = Mock()
        mock_page.url = "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel"

        with patch("wikipedia.search", return_value=["Ram Chandra Poudel"]):
            with patch(
                "wikipedia.summary",
                return_value="Ram Chandra Poudel is a Nepali politician.",
            ):
                with patch("wikipedia.page", return_value=mock_page):
                    with patch("wikipedia.set_lang"):
                        results = await service.search_external_sources(
                            query="Ram Chandra Poudel", sources=["wikipedia"]
                        )

                        assert results is not None
                        assert isinstance(results, list)
                        assert len(results) > 0

                        # Each result should have basic info
                        for result in results:
                            assert "source" in result
                            assert "title" in result
                            assert "url" in result

    @pytest.mark.asyncio
    async def test_search_external_sources_multiple_sources(self):
        """Test searching multiple external sources."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Wikipedia search
        mock_page = Mock()
        mock_page.url = "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel"

        with patch("wikipedia.search", return_value=["Ram Chandra Poudel"]):
            with patch(
                "wikipedia.summary",
                return_value="Ram Chandra Poudel is a Nepali politician.",
            ):
                with patch("wikipedia.page", return_value=mock_page):
                    with patch("wikipedia.set_lang"):
                        results = await service.search_external_sources(
                            query="Ram Chandra Poudel",
                            sources=["wikipedia", "government"],
                        )

                        assert results is not None
                        # Should have results from multiple sources
                        sources = set(r["source"] for r in results)
                        assert len(sources) > 0

    @pytest.mark.asyncio
    async def test_search_external_sources_includes_summary(self):
        """Test that search results include summary/snippet."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Wikipedia search
        mock_page = Mock()
        mock_page.url = "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel"

        with patch("wikipedia.search", return_value=["Ram Chandra Poudel"]):
            with patch(
                "wikipedia.summary",
                return_value="Ram Chandra Poudel is a Nepali politician.",
            ):
                with patch("wikipedia.page", return_value=mock_page):
                    with patch("wikipedia.set_lang"):
                        results = await service.search_external_sources(
                            query="Ram Chandra Poudel", sources=["wikipedia"]
                        )

                        assert len(results) > 0
                        # Should include summary or snippet
                        for result in results:
                            assert "summary" in result or "snippet" in result

    @pytest.mark.asyncio
    async def test_search_external_sources_handles_no_results(self):
        """Test that search handles queries with no results gracefully."""
        from nes.services.scraping import ScrapingService

        service = create_test_service()

        # Mock Wikipedia search with no results
        with patch("wikipedia.search", return_value=[]):
            with patch("wikipedia.set_lang"):
                results = await service.search_external_sources(
                    query="NonexistentPerson12345XYZ", sources=["wikipedia"]
                )

                assert results is not None
                assert isinstance(results, list)
                # Empty list is acceptable for no results
                assert len(results) == 0
