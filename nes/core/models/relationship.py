"""Relationship model using Pydantic for nes."""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .version import VersionSummary

RelationshipType = Literal[
    "AFFILIATED_WITH",
    "EMPLOYED_BY",
    "MEMBER_OF",
    "PARENT_OF",
    "CHILD_OF",
    "SUPERVISES",
    "LOCATED_IN",
    # Project-specific relationship types
    "FUNDED_BY",
    "IMPLEMENTED_BY",
    "EXECUTED_BY",
]


class Relationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_entity_id: str
    target_entity_id: str
    type: RelationshipType

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    attributes: Optional[Dict[str, Any]] = None

    version_summary: Optional[VersionSummary] = Field(
        None, description="Summary of the latest version information"
    )
    created_at: Optional[datetime] = None
    attributions: Optional[List[str]] = Field(
        None, description="Sources and attributions for the relationship data"
    )

    @field_validator("source_entity_id", "target_entity_id")
    @classmethod
    def validate_entity_ids(cls, v):
        from nes.core.identifiers import validate_entity_id as _validate_entity_id

        return _validate_entity_id(v)

    @computed_field
    @property
    def id(self) -> str:
        from nes.core.identifiers import build_relationship_id as _build_relationship_id

        return _build_relationship_id(
            self.source_entity_id, self.target_entity_id, self.type
        )
