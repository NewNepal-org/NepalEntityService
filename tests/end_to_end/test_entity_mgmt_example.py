"""End-to-end test for Entity management lifecycle."""

import shutil
import tempfile
from datetime import datetime

import pytest

from nes.core.models.base import Name
from nes.core.models.entity import Person, PoliticalParty
from nes.core.models.version import Actor, Version, VersionSummary
from nes.database.file_database import FileDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db = FileDatabase(temp_dir)
    yield db
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_entity_lifecycle_management(temp_db):
    """Test complete entity lifecycle: create, publish version, delete."""

    now = datetime.now()

    # 1. Create the actor who is performing modifications.
    actor = Actor(slug="system-user", name="System Administrator")
    await temp_db.put_actor(actor)

    # 2. Create Entity
    entity = Person(
        slug="rabindra-mishra",
        names=[
            Name(kind="DEFAULT", value="Rabindra Mishra", lang="en"),
            Name(kind="DEFAULT", value="रवीन्द्र मिश्र", lang="np"),
        ],
        createdAt=now,
        short_description="Nepali journalist and politician",
        versionSummary=VersionSummary(
            entityOrRelationshipId="entity:person/rabindra-mishra",
            type="ENTITY",
            versionNumber=1,
            actor=actor,
            changeDescription="Initial entity creation",
            createdAt=now,
        ),
    )

    created_entity = await temp_db.put_entity(entity)
    assert created_entity.id == "entity:person/rabindra-mishra"

    # Verify entity exists
    retrieved_entity = await temp_db.get_entity(entity.id)
    assert retrieved_entity is not None
    assert retrieved_entity.slug == "rabindra-mishra"
    assert len(retrieved_entity.names) == 2

    # 3. Publish the Version. This is an extension of version summary and includes snapshot and changes
    version = Version(
        **entity.versionSummary.model_dump(),
        snapshot=entity.model_dump(),
        changes={},  # TODO: Implement the differ. In this case, this would be the entire object.
    )

    published_version = await temp_db.put_version(version)
    assert published_version.id == f"version:{entity.id}:1"

    # Verify version exists
    retrieved_version = await temp_db.get_version(version.id)
    assert retrieved_version is not None
    assert retrieved_version.versionNumber == 1
    assert retrieved_version.changeDescription == "Initial entity creation"

    # 4. Update Entity and Publish New Version
    entity.short_description = "Nepali journalist, politician and media personality"
    entity.tags = ["journalist", "politician", "media"]

    version2_summary = entity.versionSummary.model_copy()
    version2_summary.versionNumber += 1
    version2_summary.changeDescription = "Updated description and added tags"
    version2_summary.createdAt = now
    version2_summary.actor = actor
    entity.versionSummary = version2_summary

    updated_entity = await temp_db.put_entity(entity)

    version_2 = Version(
        **entity.versionSummary.model_dump(),
        snapshot=entity.model_dump(),
        changes={
            "short_description": "Nepali journalist and politician",
            "tags": ["journalist", "politician", "media"],
        },  # TODO: Implement an automated diff calculator.
    )
    await temp_db.put_version(version_2)

    # Verify both versions exist
    # TODO: list_versions() should be changed to require entity_id or relationship_id parameter
    versions = await temp_db.list_versions()
    entity_versions = [v for v in versions if v.entityOrRelationshipId == entity.id]
    assert len(entity_versions) == 2

    # 5. Delete Version (for development purposes only.)
    # NOTE: we have no plans for deleting versions from the production Entity DB
    version_deleted = await temp_db.delete_version(version.id)
    assert version_deleted is True

    # Verify version is deleted
    deleted_version = await temp_db.get_version(version.id)
    assert deleted_version is None

    # 6. Delete Entity
    entity_deleted = await temp_db.delete_entity(entity.id)
    assert entity_deleted is True

    # Verify entity is deleted
    deleted_entity = await temp_db.get_entity(entity.id)
    assert deleted_entity is None

    # Verify remaining version still references deleted entity
    remaining_version = await temp_db.get_version(version_2.id)
    assert remaining_version is not None
    assert remaining_version.entityOrRelationshipId == entity.id


@pytest.mark.asyncio
async def test_organization_lifecycle(temp_db):
    """Test organization lifecycle: create, publish version, delete."""

    now = datetime.now()

    # 1. Create the actor who is performing modifications.
    actor = Actor(slug="system-user", name="System Administrator")
    await temp_db.put_actor(actor)

    # 2. Create Organization Entity
    entity = PoliticalParty(
        slug="rastriya-swatantra-party",
        names=[
            Name(kind="DEFAULT", value="Rastriya Swatantra Party", lang="en"),
            Name(kind="DEFAULT", value="राष्ट्रिय स्वतन्त्र पार्टी", lang="np"),
        ],
        createdAt=now,
        short_description="Nepali political party",
        versionSummary=VersionSummary(
            entityOrRelationshipId="entity:organization/political_party/rastriya-swatantra-party",
            type="ENTITY",
            versionNumber=1,
            actor=actor,
            changeDescription="Initial organization creation",
            createdAt=now,
        ),
    )

    created_entity = await temp_db.put_entity(entity)
    assert (
        created_entity.id
        == "entity:organization/political_party/rastriya-swatantra-party"
    )

    # Verify entity exists
    retrieved_entity = await temp_db.get_entity(entity.id)
    assert retrieved_entity is not None
    assert retrieved_entity.slug == "rastriya-swatantra-party"
    assert retrieved_entity.type == "organization"
    assert retrieved_entity.subType == "political_party"
    assert len(retrieved_entity.names) == 2

    # 3. Publish the Version
    version = Version(
        **entity.versionSummary.model_dump(),
        snapshot=entity.model_dump(),
        changes={},
    )

    published_version = await temp_db.put_version(version)
    assert published_version.id == f"version:{entity.id}:1"

    # Verify version exists
    retrieved_version = await temp_db.get_version(version.id)
    assert retrieved_version is not None
    assert retrieved_version.versionNumber == 1
    assert retrieved_version.changeDescription == "Initial organization creation"

    # 4. Delete Version
    version_deleted = await temp_db.delete_version(version.id)
    assert version_deleted is True

    # Verify version is deleted
    deleted_version = await temp_db.get_version(version.id)
    assert deleted_version is None

    # 5. Delete Entity
    entity_deleted = await temp_db.delete_entity(entity.id)
    assert entity_deleted is True

    # Verify entity is deleted
    deleted_entity = await temp_db.get_entity(entity.id)
    assert deleted_entity is None
