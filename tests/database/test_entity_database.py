"""Unit tests for EntityDatabase abstract class and implementations."""

import shutil
import tempfile
from abc import ABC
from datetime import date, datetime

import pytest

from nes.core.models.base import Name
from nes.core.models.entity import Organization, Person
from nes.core.models.relationship import Relationship
from nes.core.models.version import Actor, Version, VersionSummary
from nes.database import get_database
from nes.database.entity_database import EntityDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db = get_database(temp_dir)
    yield db
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_actor():
    """Create a sample actor for testing."""
    return Actor(slug="miraj-dhungana", name="Miraj Dhungana")


@pytest.fixture
def sample_version(sample_actor):
    """Create a sample version for testing."""
    return Version(
        entityOrRelationshipId="entity:person/harka-sampang",
        type="ENTITY",
        versionNumber=1,
        actor=sample_actor,
        changeDescription="Test version",
        createdAt=datetime.now(),
    )


@pytest.fixture
def sample_version_summary(sample_actor):
    """Create a sample version summary for testing."""
    return VersionSummary(
        entityOrRelationshipId="entity:person/harka-sampang",
        type="ENTITY",
        versionNumber=1,
        actor=sample_actor,
        changeDescription="Test version",
        createdAt=datetime.now(),
    )


@pytest.fixture
def sample_person(sample_version_summary):
    """Create a sample person entity for testing."""
    return Person(
        slug="harka-sampang",
        names=[Name(kind="DEFAULT", value="Harka Sampang", lang="ne")],
        versionSummary=sample_version_summary,
        createdAt=datetime.now(),
    )


@pytest.fixture
def sample_organization(sample_version_summary):
    """Create a sample organization entity for testing."""
    return Organization(
        slug="nepal-communist-party",
        type="organization",
        names=[Name(kind="DEFAULT", value="Nepal Communist Party", lang="ne")],
        versionSummary=sample_version_summary,
        createdAt=datetime.now(),
    )


@pytest.fixture
def sample_relationship(sample_version_summary):
    """Create a sample relationship for testing."""
    return Relationship(
        sourceEntityId="entity:person/harka-sampang",
        targetEntityId="entity:organization/nepal-communist-party",
        type="MEMBER_OF",
        startDate=date(2020, 1, 1),
        versionSummary=sample_version_summary,
        createdAt=datetime.now(),
    )


def test_entity_database_is_abstract():
    """Test that EntityDatabase is an abstract class."""
    assert issubclass(EntityDatabase, ABC)

    with pytest.raises(TypeError):
        EntityDatabase()


@pytest.mark.asyncio
async def test_complete_crud_workflow(
    temp_db,
    sample_person,
    sample_organization,
    sample_relationship,
    sample_version,
    sample_actor,
):
    """Test complete CRUD workflow for all entity types."""

    # Test Actor CRUD
    actor_result = await temp_db.put_actor(sample_actor)
    assert actor_result == sample_actor

    retrieved_actor = await temp_db.get_actor(sample_actor.id)
    assert retrieved_actor.slug == sample_actor.slug

    # Test Version CRUD
    version_result = await temp_db.put_version(sample_version)
    assert version_result == sample_version

    retrieved_version = await temp_db.get_version(sample_version.id)
    assert retrieved_version.versionNumber == sample_version.versionNumber

    # Test Entity CRUD
    person_result = await temp_db.put_entity(sample_person)
    assert person_result == sample_person

    org_result = await temp_db.put_entity(sample_organization)
    assert org_result == sample_organization

    retrieved_person = await temp_db.get_entity(sample_person.id)
    assert retrieved_person.slug == sample_person.slug

    # Test Relationship CRUD
    rel_result = await temp_db.put_relationship(sample_relationship)
    assert rel_result == sample_relationship

    retrieved_rel = await temp_db.get_relationship(sample_relationship.id)
    assert retrieved_rel.type == sample_relationship.type

    # Test List operations
    entities = await temp_db.list_entities()
    assert len(entities) == 2

    relationships = await temp_db.list_relationships()
    assert len(relationships) == 1

    versions = await temp_db.list_versions()
    assert len(versions) == 1

    actors = await temp_db.list_actors()
    assert len(actors) == 1

    # Test Delete operations
    assert await temp_db.delete_relationship(sample_relationship.id) is True
    assert await temp_db.delete_entity(sample_person.id) is True
    assert await temp_db.delete_entity(sample_organization.id) is True
    assert await temp_db.delete_version(sample_version.id) is True
    assert await temp_db.delete_actor(sample_actor.id) is True

    # Verify deletions
    assert await temp_db.get_relationship(sample_relationship.id) is None
    assert await temp_db.get_entity(sample_person.id) is None
    assert await temp_db.get_entity(sample_organization.id) is None
    assert await temp_db.get_version(sample_version.id) is None
    assert await temp_db.get_actor(sample_actor.id) is None


@pytest.mark.asyncio
async def test_pagination_consistency(temp_db, sample_version):
    """Test that pagination works consistently across all list operations."""

    # Create test data
    actors = [Actor(slug=f"actor-{i}", name=f"Actor {i}") for i in range(10)]
    for actor in actors:
        await temp_db.put_actor(actor)

    versions = []
    for i in range(10):
        version = Version(
            entityOrRelationshipId=f"entity:person/person-{i}",
            type="ENTITY",
            versionNumber=i + 1,
            actor=actors[0],
            changeDescription=f"Version {i}",
            createdAt=datetime.now(),
        )
        versions.append(version)
        await temp_db.put_version(version)

    entities = []
    for i in range(10):
        version_summary = VersionSummary(
            entityOrRelationshipId=f"entity:person/person-{i}",
            type="ENTITY",
            versionNumber=1,
            actor=actors[0],
            changeDescription=f"Person {i} version",
            createdAt=datetime.now(),
        )
        entity = Person(
            slug=f"person-{i}",
            names=[Name(kind="DEFAULT", value=f"Person {i}", lang="ne")],
            versionSummary=version_summary,
            createdAt=datetime.now(),
        )
        entities.append(entity)
        await temp_db.put_entity(entity)

    relationships = []
    for i in range(10):
        rel_version_summary = VersionSummary(
            entityOrRelationshipId=f"relationship:person-{i}:org-{i}",
            type="RELATIONSHIP",
            versionNumber=1,
            actor=actors[0],
            changeDescription=f"Relationship {i} version",
            createdAt=datetime.now(),
        )
        relationship = Relationship(
            sourceEntityId=f"entity:person/person-{i}",
            targetEntityId=f"entity:organization/org-{i}",
            type="MEMBER_OF",
            versionSummary=rel_version_summary,
            createdAt=datetime.now(),
        )
        relationships.append(relationship)
        await temp_db.put_relationship(relationship)

    # Test pagination
    page_size = 3

    # Test actors pagination
    page1_actors = await temp_db.list_actors(limit=page_size, offset=0)
    page2_actors = await temp_db.list_actors(limit=page_size, offset=page_size)
    assert len(page1_actors) == page_size
    assert len(page2_actors) == page_size

    # Test versions pagination
    page1_versions = await temp_db.list_versions(limit=page_size, offset=0)
    page2_versions = await temp_db.list_versions(limit=page_size, offset=page_size)
    assert len(page1_versions) == page_size
    assert len(page2_versions) == page_size

    # Test entities pagination
    page1_entities = await temp_db.list_entities(limit=page_size, offset=0)
    page2_entities = await temp_db.list_entities(limit=page_size, offset=page_size)
    assert len(page1_entities) == page_size
    assert len(page2_entities) == page_size

    # Test relationships pagination
    page1_rels = await temp_db.list_relationships(limit=page_size, offset=0)
    page2_rels = await temp_db.list_relationships(limit=page_size, offset=page_size)
    assert len(page1_rels) == page_size
    assert len(page2_rels) == page_size
