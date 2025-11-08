"""Schema endpoints for nes2 API.

This module provides endpoints for discovering available entity types,
subtypes, and relationship types:
- GET /api/schemas - Get entity type schemas
- GET /api/schemas/relationships - Get relationship type schemas
"""

import logging
from fastapi import APIRouter

from nes2.core.models.entity import EntityType, EntitySubType
from nes2.core.models.entity_type_map import ENTITY_TYPE_MAP
from nes2.api.responses import EntitySchemaResponse, RelationshipSchemaResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schemas", tags=["schemas"])


@router.get("", response_model=EntitySchemaResponse)
async def get_entity_schemas():
    """Get available entity types and their subtypes.
    
    Returns a structured representation of all entity types (person, organization, location)
    and their available subtypes, reflecting Nepal's political and administrative structure.
    
    Returns:
        Dictionary mapping entity types to their subtypes and descriptions
    """
    entity_types = {}
    
    # Build entity type schema
    for entity_type, subtypes in ENTITY_TYPE_MAP.items():
        type_name = entity_type.value if hasattr(entity_type, 'value') else str(entity_type)
        
        # Convert subtypes to list of strings
        subtype_list = []
        for subtype in subtypes:
            if subtype is None:
                continue
            subtype_name = subtype.value if hasattr(subtype, 'value') else str(subtype)
            subtype_list.append(subtype_name)
        
        entity_types[type_name] = {
            "subtypes": subtype_list,
            "description": _get_entity_type_description(type_name)
        }
    
    return EntitySchemaResponse(entity_types=entity_types)


@router.get("/relationships", response_model=RelationshipSchemaResponse)
async def get_relationship_schemas():
    """Get available relationship types.
    
    Returns a list of all valid relationship types that can be used
    to connect entities.
    
    Returns:
        List of relationship type names
    """
    relationship_types = [
        "AFFILIATED_WITH",
        "EMPLOYED_BY",
        "MEMBER_OF",
        "PARENT_OF",
        "CHILD_OF",
        "SUPERVISES",
        "LOCATED_IN"
    ]
    
    return RelationshipSchemaResponse(relationship_types=relationship_types)


def _get_entity_type_description(entity_type: str) -> str:
    """Get a description for an entity type.
    
    Args:
        entity_type: The entity type name
        
    Returns:
        Description string
    """
    descriptions = {
        "person": "Individuals including politicians, civil servants, and public figures",
        "organization": "Organizations including political parties, government bodies, NGOs, and international organizations",
        "location": "Geographic locations including provinces, districts, municipalities, and electoral constituencies"
    }
    
    return descriptions.get(entity_type, "")
