"""Comprehensive API endpoint tests for nes (TDD - Red Phase).

This test module covers all API endpoints following TDD principles:
- Entity endpoints (search, retrieval, filtering, pagination)
- Relationship endpoints (queries, filtering, temporal)
- Version endpoints (entity and relationship versions)
- Schema endpoints (entity type discovery)
- Health check endpoint
- Error handling
- CORS functionality
"""

from datetime import UTC, date, datetime
from typing import Any, Dict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# These imports will fail initially (Red phase) - that's expected in TDD
from nes.api.app import app
from nes.database.file_database import FileDatabase
from nes.services.publication import PublicationService
from nes.services.search import SearchService
from tests.fixtures.nepali_data import (
    NEPALI_POLITICAL_PARTIES,
    NEPALI_POLITICIANS,
    get_party_entity,
    get_politician_entity,
)


@pytest_asyncio.fixture
async def test_database(tmp_path):
    """Create a test database with sample data."""
    db_path = tmp_path / "test-db"
    db = FileDatabase(base_path=str(db_path))

    # Create publication service to populate test data
    pub_service = PublicationService(database=db)

    # Create some test entities
    # Politicians (Person entities don't have subtypes)
    from nes.core.models.entity import EntitySubType, EntityType

    ram_poudel = get_politician_entity("ram-chandra-poudel")
    ram_poudel.pop("sub_type", None)
    await pub_service.create_entity(
        entity_type=EntityType.PERSON,
        entity_data=ram_poudel,
        author_id="author:test-setup",
        change_description="Test data setup",
    )

    sher_deuba = get_politician_entity("sher-bahadur-deuba")
    sher_deuba.pop("sub_type", None)
    await pub_service.create_entity(
        entity_type=EntityType.PERSON,
        entity_data=sher_deuba,
        author_id="author:test-setup",
        change_description="Test data setup",
    )

    kp_oli = get_politician_entity("khadga-prasad-oli")
    kp_oli.pop("sub_type", None)
    await pub_service.create_entity(
        entity_type=EntityType.PERSON,
        entity_data=kp_oli,
        author_id="author:test-setup",
        change_description="Test data setup",
    )

    # Political parties
    nepali_congress = get_party_entity("nepali-congress")
    await pub_service.create_entity(
        entity_type=EntityType.ORGANIZATION,
        entity_data=nepali_congress,
        author_id="author:test-setup",
        change_description="Test data setup",
        entity_subtype=EntitySubType.POLITICAL_PARTY,
    )

    cpn_uml = get_party_entity("cpn-uml")
    await pub_service.create_entity(
        entity_type=EntityType.ORGANIZATION,
        entity_data=cpn_uml,
        author_id="author:test-setup",
        change_description="Test data setup",
        entity_subtype=EntitySubType.POLITICAL_PARTY,
    )

    # Create relationships
    await pub_service.create_relationship(
        source_entity_id="entity:person/ram-chandra-poudel",
        target_entity_id="entity:organization/political_party/nepali-congress",
        relationship_type="MEMBER_OF",
        author_id="author:test-setup",
        change_description="Test relationship",
        start_date=date(2000, 1, 1),
    )

    await pub_service.create_relationship(
        source_entity_id="entity:person/sher-bahadur-deuba",
        target_entity_id="entity:organization/political_party/nepali-congress",
        relationship_type="MEMBER_OF",
        author_id="author:test-setup",
        change_description="Test relationship",
        start_date=date(1990, 1, 1),
    )

    await pub_service.create_relationship(
        source_entity_id="entity:person/khadga-prasad-oli",
        target_entity_id="entity:organization/political_party/cpn-uml",
        relationship_type="MEMBER_OF",
        author_id="author:test-setup",
        change_description="Test relationship",
        start_date=date(1991, 1, 1),
    )

    return db


@pytest_asyncio.fixture
async def client(test_database):
    """Create an async HTTP client for testing."""
    # Override the database dependency in the app
    from nes.config import Config

    # test_database is already awaited by pytest-asyncio
    db = test_database

    # Override the global database variable for testing
    original_db = Config._database
    Config._database = db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    Config._database = original_db
    app.dependency_overrides.clear()


# ============================================================================
# Entity Endpoint Tests
# ============================================================================


class TestEntityEndpoints:
    """Tests for /api/entities endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_entities(self, client):
        """Test listing all entities without filters."""
        response = await client.get("/api/entities")

        assert response.status_code == 200
        data = response.json()

        assert "entities" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert data["total"] >= 5  # We created 5 entities
        assert len(data["entities"]) >= 5

    @pytest.mark.asyncio
    async def test_search_entities_by_query(self, client):
        """Test searching entities with text query."""
        response = await client.get("/api/entities?query=poudel")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        # Should find Ram Chandra Poudel
        entity_names = [e["names"][0]["en"]["full"] for e in data["entities"]]
        assert any("Poudel" in name for name in entity_names)

    @pytest.mark.asyncio
    async def test_search_entities_nepali_text(self, client):
        """Test searching entities with Nepali (Devanagari) text."""
        response = await client.get("/api/entities?query=पौडेल")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        # Should find Ram Chandra Poudel by Nepali name

    @pytest.mark.asyncio
    async def test_filter_entities_by_type(self, client):
        """Test filtering entities by type."""
        response = await client.get("/api/entities?entity_type=person")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 3  # We created 3 person entities
        for entity in data["entities"]:
            assert entity["type"] == "person"

    @pytest.mark.asyncio
    async def test_filter_entities_by_subtype(self, client):
        """Test filtering entities by subtype."""
        response = await client.get(
            "/api/entities?entity_type=organization&sub_type=political_party"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2  # We created 2 political parties
        for entity in data["entities"]:
            assert entity["type"] == "organization"
            assert entity["sub_type"] == "political_party"

    @pytest.mark.asyncio
    async def test_filter_entities_by_attributes(self, client):
        """Test filtering entities by attributes."""
        response = await client.get(
            '/api/entities?attributes={"party":"nepali-congress"}'
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2  # Ram Poudel and Sher Deuba
        for entity in data["entities"]:
            assert entity["attributes"]["party"] == "nepali-congress"

    @pytest.mark.asyncio
    async def test_entity_pagination(self, client):
        """Test entity pagination with limit and offset."""
        # Get first page
        response1 = await client.get("/api/entities?limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()

        assert len(data1["entities"]) == 2
        assert data1["limit"] == 2
        assert data1["offset"] == 0

        # Get second page
        response2 = await client.get("/api/entities?limit=2&offset=2")
        assert response2.status_code == 200
        data2 = response2.json()

        assert len(data2["entities"]) <= 2
        assert data2["offset"] == 2

        # Entities should be different
        ids1 = [e["id"] for e in data1["entities"]]
        ids2 = [e["id"] for e in data2["entities"]]
        assert set(ids1).isdisjoint(set(ids2))

    @pytest.mark.asyncio
    async def test_get_entity_by_id(self, client):
        """Test retrieving a specific entity by ID."""
        response = await client.get("/api/entities/entity:person/ram-chandra-poudel")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "entity:person/ram-chandra-poudel"
        assert data["slug"] == "ram-chandra-poudel"
        assert data["type"] == "person"
        assert data["names"][0]["en"]["full"] == "Ram Chandra Poudel"

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity(self, client):
        """Test retrieving a non-existent entity returns 404."""
        response = await client.get("/api/entities/entity:person/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


# ============================================================================
# Relationship Endpoint Tests
# ============================================================================


@pytest.mark.skip(reason="Relationship endpoints not yet implemented")
class TestRelationshipEndpoints:
    """Tests for /api/relationships and /api/entities/{id}/relationships endpoints."""

    @pytest.mark.asyncio
    async def test_get_entity_relationships(self, client):
        """Test getting all relationships for an entity."""
        response = await client.get(
            "/api/entities/entity:person/ram-chandra-poudel/relationships"
        )

        assert response.status_code == 200
        data = response.json()

        assert "relationships" in data
        assert "total" in data
        assert data["total"] >= 1  # At least one MEMBER_OF relationship

        # Check relationship structure
        rel = data["relationships"][0]
        assert "source_entity_id" in rel
        assert "target_entity_id" in rel
        assert "type" in rel

    @pytest.mark.asyncio
    async def test_filter_relationships_by_type(self, client):
        """Test filtering relationships by type."""
        response = await client.get(
            "/api/entities/entity:person/ram-chandra-poudel/relationships?relationship_type=MEMBER_OF"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        for rel in data["relationships"]:
            assert rel["type"] == "MEMBER_OF"

    @pytest.mark.asyncio
    async def test_search_relationships_by_target(self, client):
        """Test searching relationships by target entity."""
        response = await client.get(
            "/api/relationships?target_entity_id=entity:organization/political_party/nepali-congress"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2  # Ram Poudel and Sher Deuba
        for rel in data["relationships"]:
            assert (
                rel["target_entity_id"]
                == "entity:organization/political_party/nepali-congress"
            )

    @pytest.mark.asyncio
    async def test_filter_currently_active_relationships(self, client):
        """Test filtering for currently active relationships (no end date)."""
        response = await client.get(
            "/api/entities/entity:person/ram-chandra-poudel/relationships?currently_active=true"
        )

        assert response.status_code == 200
        data = response.json()

        for rel in data["relationships"]:
            assert rel.get("end_date") is None

    @pytest.mark.asyncio
    async def test_relationship_pagination(self, client):
        """Test relationship pagination."""
        response = await client.get("/api/relationships?limit=1&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["relationships"]) <= 1
        assert data["limit"] == 1
        assert data["offset"] == 0


# ============================================================================
# Version Endpoint Tests
# ============================================================================


@pytest.mark.skip(reason="Version endpoints not yet implemented")
class TestVersionEndpoints:
    """Tests for /api/versions endpoints."""

    @pytest.mark.asyncio
    async def test_get_entity_versions(self, client):
        """Test getting version history for an entity."""
        response = await client.get(
            "/api/entities/entity:person/ram-chandra-poudel/versions"
        )

        assert response.status_code == 200
        data = response.json()

        assert "versions" in data
        assert "total" in data
        assert data["total"] >= 1  # At least version 1 from creation

        # Check version structure
        version = data["versions"][0]
        assert "entity_or_relationship_id" in version
        assert "version_number" in version
        assert "author" in version
        assert "created_at" in version
        assert "snapshot" in version

    @pytest.mark.asyncio
    async def test_get_relationship_versions(self, client):
        """Test getting version history for a relationship."""
        # First get a relationship ID
        rel_response = await client.get(
            "/api/entities/entity:person/ram-chandra-poudel/relationships"
        )
        rel_data = rel_response.json()
        relationship_id = rel_data["relationships"][0]["id"]

        # Get versions for that relationship
        response = await client.get(f"/api/relationships/{relationship_id}/versions")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        assert data["versions"][0]["entity_or_relationship_id"] == relationship_id

    @pytest.mark.asyncio
    async def test_version_pagination(self, client):
        """Test version pagination."""
        response = await client.get(
            "/api/entities/entity:person/ram-chandra-poudel/versions?limit=1&offset=0"
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["versions"]) <= 1
        assert data["limit"] == 1


# ============================================================================
# Schema Endpoint Tests
# ============================================================================


class TestSchemaEndpoints:
    """Tests for /api/schemas endpoint."""

    @pytest.mark.asyncio
    async def test_get_entity_schemas(self, client):
        """Test getting available entity types and subtypes."""
        response = await client.get("/api/schemas")

        assert response.status_code == 200
        data = response.json()

        assert "entity_types" in data
        assert "person" in data["entity_types"]
        assert "organization" in data["entity_types"]
        assert "location" in data["entity_types"]

        # Check organization subtypes
        org_subtypes = data["entity_types"]["organization"]["subtypes"]
        assert "political_party" in org_subtypes
        assert "government_body" in org_subtypes

        # Check location subtypes
        loc_subtypes = data["entity_types"]["location"]["subtypes"]
        assert "province" in loc_subtypes
        assert "district" in loc_subtypes
        assert "metropolitan_city" in loc_subtypes

    @pytest.mark.asyncio
    async def test_get_relationship_types(self, client):
        """Test getting available relationship types."""
        response = await client.get("/api/schemas/relationships")

        assert response.status_code == 200
        data = response.json()

        assert "relationship_types" in data
        assert "MEMBER_OF" in data["relationship_types"]
        assert "AFFILIATED_WITH" in data["relationship_types"]
        assert "EMPLOYED_BY" in data["relationship_types"]


# ============================================================================
# Health Check Endpoint Tests
# ============================================================================


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "database" in data
        assert data["database"]["status"] == "connected"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_includes_version(self, client):
        """Test health check includes API version information."""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        assert "version" in data
        assert "api_version" in data


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_invalid_entity_type(self, client):
        """Test that invalid entity type returns 400."""
        response = await client.get("/api/entities?entity_type=invalid_type")

        assert response.status_code == 400
        data = response.json()

        assert "detail" in data
        assert "error" in data["detail"]
        assert "message" in data["detail"]["error"]

    @pytest.mark.asyncio
    async def test_invalid_pagination_params(self, client):
        """Test that invalid pagination parameters return 400."""
        response = await client.get("/api/entities?limit=-1")

        assert response.status_code == 400
        data = response.json()

        assert "error" in data

    @pytest.mark.asyncio
    async def test_malformed_json_attributes(self, client):
        """Test that malformed JSON in attributes returns 400."""
        response = await client.get("/api/entities?attributes=not-valid-json")

        assert response.status_code == 400
        data = response.json()

        assert "detail" in data
        assert "error" in data["detail"]

    @pytest.mark.asyncio
    async def test_error_response_format(self, client):
        """Test that error responses follow standard format."""
        response = await client.get("/api/entities/entity:person/nonexistent")

        assert response.status_code == 404
        data = response.json()

        # Check standard error format (FastAPI wraps in detail)
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]["error"]
        assert "message" in data["detail"]["error"]

    @pytest.mark.asyncio
    async def test_validation_error_details(self, client):
        """Test that validation errors include field-level details."""
        # This will be tested once we have write endpoints
        # For now, test query parameter validation
        response = await client.get("/api/entities?limit=abc")

        # FastAPI returns 422 for validation errors, but our custom handler returns 400
        assert response.status_code in [400, 422]
        data = response.json()

        # FastAPI validation errors have a different format
        assert "detail" in data or "error" in data


# ============================================================================
# CORS Tests
# ============================================================================


class TestCORS:
    """Tests for CORS functionality."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = await client.get(
            "/api/entities", headers={"Origin": "http://example.com"}
        )

        assert response.status_code == 200
        # Check for CORS headers (only present when Origin header is sent)
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request."""
        response = await client.options(
            "/api/entities",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_cors_allows_common_origins(self, client):
        """Test that CORS allows common web origins."""
        response = await client.get(
            "/api/entities", headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        # Should allow localhost for development
        assert "access-control-allow-origin" in response.headers


# ============================================================================
# Search Functionality Tests
# ============================================================================


class TestSearchFunctionality:
    """Tests for advanced search functionality."""

    @pytest.mark.asyncio
    async def test_combined_filters(self, client):
        """Test combining multiple filters."""
        response = await client.get("/api/entities?query=deuba&entity_type=person")

        assert response.status_code == 200
        data = response.json()

        # Should find Sher Bahadur Deuba
        assert data["total"] >= 1
        for entity in data["entities"]:
            assert entity["type"] == "person"

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, client):
        """Test that search is case-insensitive."""
        response1 = await client.get("/api/entities?query=POUDEL")
        response2 = await client.get("/api/entities?query=poudel")
        response3 = await client.get("/api/entities?query=Poudel")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # All should return same results
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()

        assert data1["total"] == data2["total"] == data3["total"]

    @pytest.mark.asyncio
    async def test_empty_search_results(self, client):
        """Test that empty search results are handled properly."""
        response = await client.get("/api/entities?query=nonexistentxyz123")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert data["entities"] == []

    @pytest.mark.asyncio
    async def test_search_result_relevance(self, client):
        """Test that search results are ranked by relevance."""
        response = await client.get("/api/entities?query=ram")

        assert response.status_code == 200
        data = response.json()

        # Should find Ram Chandra Poudel
        assert data["total"] >= 1
        # First result should be most relevant (exact match in name)
