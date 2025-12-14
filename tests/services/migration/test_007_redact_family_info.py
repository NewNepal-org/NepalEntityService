"""
Test for migration 007-redact-family-info.

This module tests that the migration correctly redacts family information
from PersonDetails.
"""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from nes.core.models.base import (
    LangText,
    LangTextValue,
    Name,
    NameKind,
    ProvenanceMethod,
)
from nes.core.models.person import Person, PersonDetails
from nes.core.models.version import Author, VersionSummary, VersionType
from nes.services.migration import MigrationContext


@pytest.mark.asyncio
async def test_redact_family_info_migration():
    """Test that the migration correctly redacts family information."""
    # Import the migration
    import importlib.util

    migration_path = (
        Path(__file__).parent.parent.parent.parent
        / "migrations"
        / "007-redact-family-info"
    )
    migrate_file = migration_path / "migrate.py"

    spec = importlib.util.spec_from_file_location("migrate_007", migrate_file)
    migrate_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migrate_module)

    migrate = migrate_module.migrate

    # Create mock services
    mock_publication = Mock()
    mock_publication.update_entity = AsyncMock(return_value=None)

    # Create test person entities with family information
    person_with_family = Person(
        slug="test-person-1",
        type="person",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Test Person 1"})],
        personal_details=PersonDetails(
            spouse_name=LangText(
                en=LangTextValue(value="Test Spouse", provenance=ProvenanceMethod.HUMAN)
            ),
            mother_name=LangText(
                en=LangTextValue(value="Test Mother", provenance=ProvenanceMethod.HUMAN)
            ),
            father_name=LangText(
                en=LangTextValue(value="Test Father", provenance=ProvenanceMethod.HUMAN)
            ),
        ),
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/test-person-1",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    person_without_family = Person(
        slug="test-person-2",
        type="person",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Test Person 2"})],
        personal_details=PersonDetails(gender="male"),
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/test-person-2",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    person_no_details = Person(
        slug="test-person-3",
        type="person",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Test Person 3"})],
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/test-person-3",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    # Create mock database
    mock_db = Mock()
    mock_db.list_entities = Mock(
        return_value=[person_with_family, person_without_family, person_no_details]
    )

    # Create migration context
    with tempfile.TemporaryDirectory() as tmpdir:
        context = MigrationContext(
            publication_service=mock_publication,
            search_service=Mock(),
            scraping_service=Mock(),
            db=mock_db,
            migration_dir=Path(tmpdir),
        )

        # Run the migration
        await migrate(context)

        # Verify that update_entity was called exactly once (for person_with_family)
        assert mock_publication.update_entity.call_count == 1

        # Verify the person with family info was updated
        call_args = mock_publication.update_entity.call_args
        updated_entity = call_args.kwargs["entity"]
        assert updated_entity.slug == "test-person-1"
        assert updated_entity.personal_details.spouse_name is None
        assert updated_entity.personal_details.mother_name is None
        assert updated_entity.personal_details.father_name is None

        # Verify the change description
        assert (
            call_args.kwargs["change_description"]
            == "Redact family information for privacy"
        )

        # Verify logs
        assert len(context.logs) == 5  # Start, found, updated, skipped, completed
        assert "3 person entities" in context.logs[1]
        assert "Updated 1 person entities" in context.logs[2]
        assert "Skipped 2 person entities" in context.logs[3]
