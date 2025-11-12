"""Tests for Search Service in nes.

Following TDD approach: Write failing tests first (Red phase).
These tests define the expected behavior of the Search Service.

The Search Service provides read-optimized search capabilities for:
- Entity text search with multilingual support (Nepali and English)
- Type and subtype filtering
- Attribute-based filtering
- Pagination
- Relationship search with temporal filtering
- Version retrieval
"""

from datetime import UTC, date, datetime
from typing import Optional

import pytest

from nes.core.models.base import Name, NameKind
from nes.core.models.entity import EntitySubType, EntityType
from nes.core.models.organization import PoliticalParty
from nes.core.models.person import Person
from nes.core.models.relationship import Relationship
from nes.core.models.version import Author, Version, VersionSummary, VersionType
from nes.database.file_database import FileDatabase


class TestSearchServiceFoundation:
    """Test Search Service initialization and basic structure."""

    @pytest.mark.asyncio
    async def test_search_service_initialization(self, temp_db_path):
        """Test that SearchService can be initialized with a database."""
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        service = SearchService(database=db)

        assert service is not None
        assert service.database == db

    @pytest.mark.asyncio
    async def test_search_service_requires_database(self):
        """Test that SearchService requires a database instance."""
        from nes.services.search import SearchService

        with pytest.raises(TypeError):
            SearchService()


class TestSearchServiceEntityTextSearch:
    """Test entity text search capabilities."""

    @pytest.mark.asyncio
    async def test_search_entities_with_text_query(self, temp_db_path):
        """Test basic text search across entity names."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create test entities
        await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "ram-poudel",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Ram Chandra Poudel"}}],
            },
            "author:test",
            "Test",
        )
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "sher-deuba",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Sher Bahadur Deuba"}}],
            },
            "author:test",
            "Test",
        )

        # Search for "ram"
        results = await search_service.search_entities(query="ram")

        assert len(results) == 1
        assert results[0].slug == "ram-poudel"

    @pytest.mark.asyncio
    async def test_search_entities_case_insensitive(self, temp_db_path):
        """Test that search is case-insensitive."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entity
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "test-person",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Ram Chandra Poudel"}}],
            },
            "author:test",
            "Test",
        )

        # Search with different cases
        results_lower = await search_service.search_entities(query="ram")
        results_upper = await search_service.search_entities(query="RAM")
        results_mixed = await search_service.search_entities(query="Ram")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    @pytest.mark.asyncio
    async def test_search_entities_substring_matching(self, temp_db_path):
        """Test that search supports substring matching."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entity
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "test-person",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Ram Chandra Poudel"}}],
            },
            "author:test",
            "Test",
        )

        # Search with substring
        results = await search_service.search_entities(query="poudel")

        assert len(results) == 1
        assert results[0].slug == "test-person"


class TestSearchServiceMultilingualSearch:
    """Test multilingual search (Nepali and English)."""

    @pytest.mark.asyncio
    async def test_search_entities_nepali_text(self, temp_db_path):
        """Test search with Nepali (Devanagari) text."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entity with Nepali name
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "ram-poudel",
                "type": "person",
                "names": [
                    {
                        "kind": "PRIMARY",
                        "en": {"full": "Ram Chandra Poudel"},
                        "ne": {"full": "राम चन्द्र पौडेल"},
                    }
                ],
            },
            "author:test",
            "Test",
        )

        # Search with Nepali text
        results = await search_service.search_entities(query="राम")

        assert len(results) == 1
        assert results[0].slug == "ram-poudel"

    @pytest.mark.asyncio
    async def test_search_entities_both_languages(self, temp_db_path):
        """Test that search works across both English and Nepali names."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entity with both English and Nepali names
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "test-person",
                "type": "person",
                "names": [
                    {
                        "kind": "PRIMARY",
                        "en": {"full": "Ram Chandra Poudel"},
                        "ne": {"full": "राम चन्द्र पौडेल"},
                    }
                ],
            },
            "author:test",
            "Test",
        )

        # Search with English
        results_en = await search_service.search_entities(query="ram")
        assert len(results_en) == 1

        # Search with Nepali
        results_ne = await search_service.search_entities(query="पौडेल")
        assert len(results_ne) == 1


class TestSearchServiceTypeFiltering:
    """Test type and subtype filtering."""

    @pytest.mark.asyncio
    async def test_search_entities_filter_by_type(self, temp_db_path):
        """Test filtering entities by type."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities of different types
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Test Person"}}],
            },
            "author:test",
            "Test",
        )
        await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Test Party"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Search with type filter
        results = await search_service.search_entities(entity_type="person")

        assert len(results) == 1
        assert results[0].type == EntityType.PERSON

    @pytest.mark.asyncio
    async def test_search_entities_filter_by_subtype(self, temp_db_path):
        """Test filtering entities by subtype."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create organizations with different subtypes
        await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "party-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Party 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )
        await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "gov-1",
                "type": "organization",
                "sub_type": "government_body",
                "names": [{"kind": "PRIMARY", "en": {"full": "Gov Body 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.GOVERNMENT_BODY,
        )

        # Search with subtype filter
        results = await search_service.search_entities(
            entity_type="organization", sub_type="political_party"
        )

        assert len(results) == 1
        assert results[0].sub_type == EntitySubType.POLITICAL_PARTY

    @pytest.mark.asyncio
    async def test_search_entities_type_and_query(self, temp_db_path):
        """Test combining type filter with text query."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "ram-person",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Ram Poudel"}}],
            },
            "author:test",
            "Test",
        )
        await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "ram-org",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Ram Party"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Search with type filter and query
        results = await search_service.search_entities(
            query="ram", entity_type="person"
        )

        assert len(results) == 1
        assert results[0].type == EntityType.PERSON


class TestSearchServiceAttributeFiltering:
    """Test attribute-based filtering."""

    @pytest.mark.asyncio
    async def test_search_entities_filter_by_attributes(self, temp_db_path):
        """Test filtering entities by attributes."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities with different attributes
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
                "attributes": {"party": "nepali-congress"},
            },
            "author:test",
            "Test",
        )
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-2",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 2"}}],
                "attributes": {"party": "cpn-uml"},
            },
            "author:test",
            "Test",
        )

        # Search with attribute filter
        results = await search_service.search_entities(
            attributes={"party": "nepali-congress"}
        )

        assert len(results) == 1
        assert results[0].slug == "person-1"

    @pytest.mark.asyncio
    async def test_search_entities_multiple_attribute_filters(self, temp_db_path):
        """Test filtering with multiple attributes (AND logic)."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities with different attribute combinations
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
                "attributes": {"party": "nepali-congress", "position": "minister"},
            },
            "author:test",
            "Test",
        )
        await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-2",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 2"}}],
                "attributes": {"party": "nepali-congress", "position": "member"},
            },
            "author:test",
            "Test",
        )

        # Search with multiple attribute filters (AND logic)
        results = await search_service.search_entities(
            attributes={"party": "nepali-congress", "position": "minister"}
        )

        assert len(results) == 1
        assert results[0].slug == "person-1"


class TestSearchServicePagination:
    """Test pagination support."""

    @pytest.mark.asyncio
    async def test_search_entities_with_limit(self, temp_db_path):
        """Test limiting search results."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create multiple entities
        for i in range(5):
            await pub_service.create_entity(
                EntityType.PERSON,
                {
                    "slug": f"person-{i}",
                    "type": "person",
                    "names": [{"kind": "PRIMARY", "en": {"full": f"Person {i}"}}],
                },
                "author:test",
                "Test",
            )

        # Search with limit
        results = await search_service.search_entities(limit=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_entities_with_offset(self, temp_db_path):
        """Test offset-based pagination."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create multiple entities
        for i in range(5):
            await pub_service.create_entity(
                EntityType.PERSON,
                {
                    "slug": f"person-{i}",
                    "type": "person",
                    "names": [{"kind": "PRIMARY", "en": {"full": f"Person {i}"}}],
                },
                "author:test",
                "Test",
            )

        # Get first page
        page1 = await search_service.search_entities(limit=2, offset=0)
        # Get second page
        page2 = await search_service.search_entities(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        # Ensure different results
        assert page1[0].slug != page2[0].slug

    @pytest.mark.asyncio
    async def test_search_entities_pagination_with_query(self, temp_db_path):
        """Test pagination with text query."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create multiple entities with "test" in name
        for i in range(5):
            await pub_service.create_entity(
                EntityType.PERSON,
                {
                    "slug": f"test-{i}",
                    "type": "person",
                    "names": [{"kind": "PRIMARY", "en": {"full": f"Test Person {i}"}}],
                },
                "author:test",
                "Test",
            )

        # Search with query and pagination
        results = await search_service.search_entities(query="test", limit=3, offset=0)

        assert len(results) == 3


class TestSearchServiceRelationshipSearch:
    """Test relationship search capabilities."""

    @pytest.mark.asyncio
    async def test_search_relationships_by_type(self, temp_db_path):
        """Test searching relationships by type."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities
        person = await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
            },
            "author:test",
            "Test",
        )
        org = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Create relationships of different types
        await pub_service.create_relationship(
            person.id, org.id, "MEMBER_OF", "author:test", "Test"
        )
        await pub_service.create_relationship(
            person.id, org.id, "AFFILIATED_WITH", "author:test", "Test"
        )

        # Search by relationship type
        results = await search_service.search_relationships(
            relationship_type="MEMBER_OF"
        )

        assert len(results) == 1
        assert results[0].type == "MEMBER_OF"

    @pytest.mark.asyncio
    async def test_search_relationships_by_source_entity(self, temp_db_path):
        """Test searching relationships by source entity."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities
        person1 = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
            },
            "author:test",
            "Test",
        )
        person2 = await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-2",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 2"}}],
            },
            "author:test",
            "Test",
        )
        org = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Create relationships
        await pub_service.create_relationship(
            person1.id, org.id, "MEMBER_OF", "author:test", "Test"
        )
        await pub_service.create_relationship(
            person2.id, org.id, "MEMBER_OF", "author:test", "Test"
        )

        # Search by source entity
        results = await search_service.search_relationships(source_entity_id=person1.id)

        assert len(results) == 1
        assert results[0].source_entity_id == person1.id

    @pytest.mark.asyncio
    async def test_search_relationships_by_target_entity(self, temp_db_path):
        """Test searching relationships by target entity."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities
        person = await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
            },
            "author:test",
            "Test",
        )
        org1 = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )
        org2 = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-2",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 2"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Create relationships
        await pub_service.create_relationship(
            person.id, org1.id, "MEMBER_OF", "author:test", "Test"
        )
        await pub_service.create_relationship(
            person.id, org2.id, "AFFILIATED_WITH", "author:test", "Test"
        )

        # Search by target entity
        results = await search_service.search_relationships(target_entity_id=org1.id)

        assert len(results) == 1
        assert results[0].target_entity_id == org1.id


class TestSearchServiceTemporalFiltering:
    """Test temporal filtering for relationships."""

    @pytest.mark.asyncio
    async def test_search_relationships_active_on_date(self, temp_db_path):
        """Test filtering relationships active on a specific date."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities
        person = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
            },
            "author:test",
            "Test",
        )
        org = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Create relationships with different date ranges
        await pub_service.create_relationship(
            person.id,
            org.id,
            "MEMBER_OF",
            "author:test",
            "Test",
            start_date=date(2020, 1, 1),
            end_date=date(2022, 12, 31),
        )
        await pub_service.create_relationship(
            person.id,
            org.id,
            "AFFILIATED_WITH",
            "author:test",
            "Test",
            start_date=date(2023, 1, 1),
        )

        # Search for relationships active on 2021-06-01
        results = await search_service.search_relationships(
            source_entity_id=person.id, active_on=date(2021, 6, 1)
        )

        assert len(results) == 1
        assert results[0].type == "MEMBER_OF"

    @pytest.mark.asyncio
    async def test_search_relationships_currently_active(self, temp_db_path):
        """Test filtering for currently active relationships (no end date)."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities
        person = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
            },
            "author:test",
            "Test",
        )
        org = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        # Create relationships - one ended, one active
        await pub_service.create_relationship(
            person.id,
            org.id,
            "MEMBER_OF",
            "author:test",
            "Test",
            start_date=date(2020, 1, 1),
            end_date=date(2022, 12, 31),
        )
        await pub_service.create_relationship(
            person.id,
            org.id,
            "AFFILIATED_WITH",
            "author:test",
            "Test",
            start_date=date(2023, 1, 1),
        )

        # Search for currently active relationships
        results = await search_service.search_relationships(
            source_entity_id=person.id, currently_active=True
        )

        assert len(results) == 1
        assert results[0].type == "AFFILIATED_WITH"
        assert results[0].end_date is None


class TestSearchServiceVersionRetrieval:
    """Test version retrieval capabilities."""

    @pytest.mark.asyncio
    async def test_get_entity_versions(self, temp_db_path):
        """Test retrieving version history for an entity."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create and update entity
        entity = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "test-person",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Test Person"}}],
            },
            "author:test",
            "Initial",
        )

        entity.attributes = {"update": "1"}
        await pub_service.update_entity(entity, "author:test", "Update 1")

        entity.attributes = {"update": "2"}
        await pub_service.update_entity(entity, "author:test", "Update 2")

        # Get versions
        versions = await search_service.get_entity_versions(entity_id=entity.id)

        assert len(versions) == 3
        assert versions[0].version_number == 1
        assert versions[1].version_number == 2
        assert versions[2].version_number == 3

    @pytest.mark.asyncio
    async def test_get_relationship_versions(self, temp_db_path):
        """Test retrieving version history for a relationship."""
        from nes.services.publication import PublicationService
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        pub_service = PublicationService(database=db)
        search_service = SearchService(database=db)

        # Create entities and relationship
        person = await pub_service.create_entity(
            EntityType.PERSON,
            {
                "slug": "person-1",
                "type": "person",
                "names": [{"kind": "PRIMARY", "en": {"full": "Person 1"}}],
            },
            "author:test",
            "Test",
        )
        org = await pub_service.create_entity(
            EntityType.ORGANIZATION,
            {
                "slug": "org-1",
                "type": "organization",
                "sub_type": "political_party",
                "names": [{"kind": "PRIMARY", "en": {"full": "Org 1"}}],
            },
            "author:test",
            "Test",
            EntitySubType.POLITICAL_PARTY,
        )

        relationship = await pub_service.create_relationship(
            person.id, org.id, "MEMBER_OF", "author:test", "Initial"
        )

        # Update relationship
        relationship.attributes = {"role": "member"}
        await pub_service.update_relationship(relationship, "author:test", "Update 1")

        # Get versions
        versions = await search_service.get_relationship_versions(
            relationship_id=relationship.id
        )

        assert len(versions) == 2
        assert versions[0].version_number == 1
        assert versions[1].version_number == 2

    @pytest.mark.asyncio
    async def test_get_entity_versions_returns_empty_for_nonexistent(
        self, temp_db_path
    ):
        """Test that getting versions for nonexistent entity returns empty list."""
        from nes.services.search import SearchService

        db = FileDatabase(base_path=str(temp_db_path))
        search_service = SearchService(database=db)

        versions = await search_service.get_entity_versions(
            entity_id="entity:person/nonexistent"
        )

        assert versions == []
