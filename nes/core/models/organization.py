"""Organization-specific models for nes."""

from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import Address, LangText
from .entity import Entity, EntitySubType


class GovernmentType(str, Enum):
    """Types of government entities."""

    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    LOCAL = "local"
    OTHER = "other"
    UNKNOWN = "unknown"


class Organization(Entity):
    """Organization entity."""

    type: Literal["organization"] = Field(
        default="organization", description="Entity type, always organization"
    )


class PartySymbol(BaseModel):
    """Political party symbol."""

    model_config = ConfigDict(extra="forbid")

    name: LangText = Field(..., description="Symbol name")


class PoliticalParty(Organization):
    """Political party organization.

    Note: party_chief is a temporary field for storing party leadership as text.
    Use relationships to properly link party members and leadership roles.
    """

    sub_type: Literal[EntitySubType.POLITICAL_PARTY] = Field(
        default=EntitySubType.POLITICAL_PARTY,
        description="Organization subtype, always political_party",
    )
    address: Optional[Address] = Field(None, description="Party headquarters address")
    party_chief: Optional[LangText] = Field(
        None, description="Party chief or main official"
    )
    registration_date: Optional[date] = Field(
        None, description="Party registration date"
    )
    symbol: Optional[PartySymbol] = Field(None, description="Party electoral symbol")


class GovernmentBody(Organization):
    """Government body organization."""

    sub_type: Literal[EntitySubType.GOVERNMENT_BODY] = Field(
        default=EntitySubType.GOVERNMENT_BODY,
        description="Organization subtype, always government_body",
    )
    government_type: Optional[GovernmentType] = Field(
        None, description="Type of government (federal, provincial, local)"
    )
