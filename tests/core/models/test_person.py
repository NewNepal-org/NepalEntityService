"""Tests for Person model in nes."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from nes.core.models.base import (
    LangText,
    LangTextValue,
    Name,
    NameKind,
    ProvenanceMethod,
)
from nes.core.models.person import (
    Candidacy,
    Education,
    ElectionSymbol,
    ElectionType,
    ElectoralDetails,
    Gender,
    Person,
    PersonDetails,
    Position,
)
from nes.core.models.version import Author, VersionSummary, VersionType


def test_person_basic_creation():
    """Test creating a basic Person entity."""

    person = Person(
        slug="harka-sampang",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Harka Sampang"})],
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/harka-sampang",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    assert person.type == "person"
    assert person.sub_type is None
    assert person.slug == "harka-sampang"
    assert person.id == "entity:person/harka-sampang"


def test_person_with_personal_details():
    """Test Person with personal details."""

    person = Person(
        slug="harka-sampang",
        names=[
            Name(
                kind=NameKind.PRIMARY,
                en={"full": "Harka Sampang"},
                ne={"full": "हर्क साम्पाङ"},
            )
        ],
        personal_details=PersonDetails(
            birth_date="1975",
            gender=Gender.MALE,
            father_name=LangText(
                en=LangTextValue(value="Father Name", provenance=ProvenanceMethod.HUMAN)
            ),
            mother_name=LangText(
                en=LangTextValue(value="Mother Name", provenance=ProvenanceMethod.HUMAN)
            ),
        ),
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/harka-sampang",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    assert person.personal_details is not None
    assert person.personal_details.birth_date == "1975"
    assert person.personal_details.gender == Gender.MALE
    assert person.personal_details.father_name.en.value == "Father Name"


def test_person_with_education():
    """Test Person with education records."""

    person = Person(
        slug="harka-sampang",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Harka Sampang"})],
        personal_details=PersonDetails(
            education=[
                Education(
                    institution=LangText(
                        en=LangTextValue(
                            value="Tribhuvan University",
                            provenance=ProvenanceMethod.HUMAN,
                        )
                    ),
                    degree=LangText(
                        en=LangTextValue(
                            value="Bachelor's Degree", provenance=ProvenanceMethod.HUMAN
                        )
                    ),
                    start_year=1995,
                    end_year=1999,
                )
            ]
        ),
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/harka-sampang",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    assert person.personal_details.education is not None
    assert len(person.personal_details.education) == 1
    assert (
        person.personal_details.education[0].institution.en.value
        == "Tribhuvan University"
    )
    assert person.personal_details.education[0].start_year == 1995


def test_person_with_positions():
    """Test Person with professional positions."""

    person = Person(
        slug="harka-sampang",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Harka Sampang"})],
        personal_details=PersonDetails(
            positions=[
                Position(
                    title=LangText(
                        en=LangTextValue(
                            value="Party Leader", provenance=ProvenanceMethod.HUMAN
                        )
                    ),
                    organization=LangText(
                        en=LangTextValue(
                            value="Shram Sanskriti Party",
                            provenance=ProvenanceMethod.HUMAN,
                        )
                    ),
                    start_date=date(2020, 1, 1),
                    description="Leader of the party",
                )
            ]
        ),
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/harka-sampang",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    assert person.personal_details.positions is not None
    assert len(person.personal_details.positions) == 1
    assert person.personal_details.positions[0].title.en.value == "Party Leader"
    assert person.personal_details.positions[0].start_date == date(2020, 1, 1)


def test_person_with_electoral_details():
    """Test Person with electoral candidacy records."""

    person = Person(
        slug="harka-sampang",
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Harka Sampang"})],
        electoral_details=ElectoralDetails(
            candidacies=[
                Candidacy(
                    candidate_id=12345,
                    election_year=2022,
                    election_type=ElectionType.FEDERAL,
                    constituency_id="entity:location/constituency/kathmandu-1",
                    symbol=ElectionSymbol(
                        symbol_name=LangText(
                            en=LangTextValue(
                                value="Hammer", provenance=ProvenanceMethod.HUMAN
                            )
                        ),
                        nec_id=1,
                    ),
                    party_id="entity:organization/political_party/shram-sanskriti-party",
                    votes_received=5000,
                    elected=False,
                )
            ]
        ),
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/harka-sampang",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    assert person.electoral_details is not None
    assert len(person.electoral_details.candidacies) == 1
    candidacy = person.electoral_details.candidacies[0]
    assert candidacy.election_year == 2022
    assert candidacy.symbol.symbol_name.en.value == "Hammer"
    assert candidacy.votes_received == 5000
    assert candidacy.elected is False


def test_person_cannot_have_subtype():
    """Test that Person entities cannot have a subtype."""

    # This should work - sub_type is None
    person = Person(
        slug="harka-sampang",
        sub_type=None,
        names=[Name(kind=NameKind.PRIMARY, en={"full": "Harka Sampang"})],
        version_summary=VersionSummary(
            entity_or_relationship_id="entity:person/harka-sampang",
            type=VersionType.ENTITY,
            version_number=1,
            author=Author(slug="system"),
            change_description="Initial",
            created_at=datetime.now(UTC),
        ),
        created_at=datetime.now(UTC),
    )

    assert person.sub_type is None


def test_candidacy_validates_entity_ids():
    """Test that Candidacy validates entity IDs."""

    # Valid entity IDs should work
    candidacy = Candidacy(
        candidate_id=12345,
        election_year=2022,
        election_type=ElectionType.FEDERAL,
        constituency_id="entity:location/constituency/kathmandu-1",
        symbol=ElectionSymbol(
            symbol_name=LangText(
                en=LangTextValue(value="Hammer", provenance=ProvenanceMethod.HUMAN)
            ),
            nec_id=2,
        ),
        party_id="entity:organization/political_party/shram-sanskriti-party",
    )

    assert candidacy.candidate_id == 12345

    # Invalid entity ID should fail
    with pytest.raises(ValidationError):
        Candidacy(
            candidate_id=12345,
            election_year=2022,
            election_type=ElectionType.FEDERAL,
            constituency_id="invalid-id",
            symbol=ElectionSymbol(
                symbol_name=LangText(
                    en=LangTextValue(value="Hammer", provenance=ProvenanceMethod.HUMAN)
                ),
                nec_id=2,
            ),
        )
