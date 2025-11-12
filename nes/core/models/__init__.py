"""Core models for Nepal Entity Service v2."""

from .base import (
    Address,
    Attribution,
    Contact,
    ContactType,
    EntityPicture,
    EntityPictureType,
    LangText,
    LangTextValue,
    Name,
    NameKind,
    NameParts,
    ProvenanceMethod,
)
from .entity import (
    Entity,
    EntitySubType,
    EntityType,
    ExternalIdentifier,
    IdentifierScheme,
)
from .location import ADMINISTRATIVE_LEVELS, Location, LocationType
from .organization import (
    GovernmentBody,
    GovernmentType,
    Organization,
    PartySymbol,
    PoliticalParty,
)
from .person import (
    Candidacy,
    Education,
    ElectoralDetails,
    Gender,
    Person,
    PersonDetails,
    Position,
    Symbol,
)
from .relationship import Relationship, RelationshipType
from .version import Author, Version, VersionSummary, VersionType

__all__ = [
    # Base models
    "Address",
    "Attribution",
    "Contact",
    "ContactType",
    "EntityPicture",
    "EntityPictureType",
    "LangText",
    "LangTextValue",
    "Name",
    "NameKind",
    "NameParts",
    "ProvenanceMethod",
    # Entity models
    "Entity",
    "EntitySubType",
    "EntityType",
    "ExternalIdentifier",
    "IdentifierScheme",
    # Person models
    "Person",
    "PersonDetails",
    "Gender",
    "Education",
    "Position",
    "ElectoralDetails",
    "Candidacy",
    "Symbol",
    # Organization models
    "Organization",
    "PoliticalParty",
    "PartySymbol",
    "GovernmentBody",
    "GovernmentType",
    # Location models
    "Location",
    "LocationType",
    "ADMINISTRATIVE_LEVELS",
    # Relationship models
    "Relationship",
    "RelationshipType",
    # Version models
    "Author",
    "Version",
    "VersionSummary",
    "VersionType",
]
