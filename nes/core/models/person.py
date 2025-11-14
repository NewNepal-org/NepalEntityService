"""Person-specific models for nes."""

from datetime import date
from enum import Enum
from typing import List, Literal, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator

from .base import Address, LangText
from .entity import Entity


class Gender(str, Enum):
    """Gender enumeration."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ElectionType(str, Enum):
    """Election type enumeration."""

    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    LOCAL = "local"  # Municipal, etc. for mayor/deputy mayor
    WARD = "ward"


class ElectionPosition(str, Enum):
    """Election position enumeration."""

    FEDERAL_PARLIAMENT = "federal_parliament"
    PROVINCIAL_ASSEMBLY = "provincial_assembly"
    MAYOR = "mayor"
    DEPUTY_MAYOR = "deputy_mayor"
    WARD_CHAIRPERSON = "ward_chairperson"
    WARD_MEMBER = "ward_member"
    DALIT_FEMALE_MEMBER = "dalit_female_member"
    FEMALE_MEMBER = "female_member"


class Education(BaseModel):
    """Education record for a person."""

    model_config = ConfigDict(extra="forbid")

    institution: LangText = Field(
        ..., description="Name of the educational institution"
    )
    degree: Optional[LangText] = Field(
        None, description="Degree or qualification obtained"
    )
    field: Optional[LangText] = Field(None, description="Field of study")
    start_year: Optional[int] = Field(None, description="Year education started")
    end_year: Optional[int] = Field(None, description="Year education completed")


class Position(BaseModel):
    """Position or role held by a person."""

    model_config = ConfigDict(extra="forbid")

    title: LangText = Field(..., description="Job title or position name")
    organization: Optional[LangText] = Field(
        None, description="Organization or company name"
    )
    start_date: Optional[date] = Field(None, description="Start date of the position")
    end_date: Optional[date] = Field(None, description="End date of the position")
    description: Optional[str] = Field(
        None, max_length=200, description="Description of the position"
    )


class PersonDetails(BaseModel):
    """Personal details for a person."""

    model_config = ConfigDict(extra="forbid")

    birth_date: Optional[str] = Field(  # "2012", "2012-01", "2012-01-01"
        None, description="Birth date (may be partial, e.g., year only)"
    )
    birth_place: Optional[Address] = Field(None, description="Place of birth")
    citizenship_place: Optional[Address] = Field(
        None, description="Citizenship place, usually district"
    )
    gender: Optional[Gender] = Field(None, description="Gender")
    address: Optional[Address] = Field(None, description="Current address")
    father_name: Optional[LangText] = Field(None, description="Father's name")
    mother_name: Optional[LangText] = Field(None, description="Mother's name")
    spouse_name: Optional[LangText] = Field(None, description="Spouse's name")

    education: Optional[List[Education]] = Field(
        None, description="Educational background"
    )
    positions: Optional[List[Position]] = Field(
        None, description="Professional positions held"
    )


class ElectionSymbol(BaseModel):
    """Election symbol information."""

    model_config = ConfigDict(extra="forbid")

    symbol_name: LangText = Field(..., description="Symbol name")
    nec_id: Optional[int] = Field(
        ..., description="Nepal Election Commission symbol ID"
    )
    url: Optional[AnyUrl] = Field(None, description="URL to symbol image")


class Candidacy(BaseModel):
    """Electoral candidacy record."""

    model_config = ConfigDict(extra="forbid")

    election_year: int = Field(..., description="Election year")
    election_type: ElectionType = Field(
        ..., description="Election type: federal, provincial, local"
    )
    constituency_id: str = Field(
        ...,
        description="The full constituency mapping where the election took place. For federal/provincial elections, it will be an election constituency. For local elections, it will be the local area (village/municipality/etc). For ward elections, it will be the ward ID.",
    )
    pa_subdivision: Optional[str] = Field(
        None, description="Provincial Assembly Election Subdivision (A or B)."
    )
    position: Optional[ElectionPosition] = Field(
        None, description="Position contested in the election."
    )

    candidate_id: int = Field(..., description="Nepal Election Commission candidate ID")
    party_id: Optional[str] = Field(None, description="Party entity ID")
    votes_received: Optional[int] = Field(None, description="Number of votes received")
    elected: Optional[bool] = Field(None, description="Whether candidate was elected")
    symbol: Optional[ElectionSymbol] = Field(None, description="Election symbol used")

    @field_validator("party_id", "constituency_id")
    @classmethod
    def validate_entity_ids(cls, v: Optional[str]) -> Optional[str]:
        from nes.core.identifiers.validators import is_valid_entity_id

        if v is None:
            return v

        if not is_valid_entity_id(v):
            raise ValueError("Must be a valid entity ID")
        return v


class ElectoralDetails(BaseModel):
    """Electoral details for a person."""

    model_config = ConfigDict(extra="forbid")

    candidacies: Optional[List[Candidacy]] = Field(
        None, description="List of electoral candidacies"
    )


class Person(Entity):
    """Person entity. Note: Person entities do not have subtypes."""

    type: Literal["person"] = Field(
        default="person", description="Entity type, always person"
    )
    sub_type: Literal[None] = Field(
        default=None, description="Person entities do not have subtypes"
    )
    personal_details: Optional[PersonDetails] = Field(
        None, description="Personal details"
    )
    electoral_details: Optional[ElectoralDetails] = Field(
        None, description="Electoral details"
    )
