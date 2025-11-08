"""Relationship endpoints for nes2 API.

This module provides endpoints for relationship search and version retrieval:
- GET /api/relationships - Search relationships with filtering
- GET /api/relationships/{relationship_id}/versions - Get version history for a relationship
"""

import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from nes2.services.search import SearchService
from nes2.api.app import get_search_service
from nes2.api.responses import RelationshipListResponse, VersionListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/relationships", tags=["relationships"])


@router.get("", response_model=RelationshipListResponse)
async def search_relationships(
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    source_entity_id: Optional[str] = Query(None, description="Filter by source entity ID"),
    target_entity_id: Optional[str] = Query(None, description="Filter by target entity ID"),
    currently_active: Optional[bool] = Query(None, description="Filter for currently active relationships"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    search_service: SearchService = Depends(get_search_service)
):
    """Search relationships with filtering and temporal queries.
    
    Supports filtering by:
    - Relationship type (e.g., MEMBER_OF, AFFILIATED_WITH)
    - Source entity ID
    - Target entity ID
    - Currently active (no end date)
    
    Examples:
        - /api/relationships - List all relationships
        - /api/relationships?relationship_type=MEMBER_OF - Filter by type
        - /api/relationships?target_entity_id=entity:organization/political_party/nepali-congress - Filter by target
        - /api/relationships?currently_active=true - Only active relationships
    """
    # Validate relationship_type if provided
    valid_types = [
        "AFFILIATED_WITH", "EMPLOYED_BY", "MEMBER_OF", "PARENT_OF",
        "CHILD_OF", "SUPERVISES", "LOCATED_IN"
    ]
    if relationship_type and relationship_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_RELATIONSHIP_TYPE",
                    "message": f"Invalid relationship_type: {relationship_type}. Must be one of: {', '.join(valid_types)}"
                }
            }
        )
    
    try:
        relationships = await search_service.search_relationships(
            relationship_type=relationship_type,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            currently_active=currently_active,
            limit=limit,
            offset=offset
        )
        
        # Convert relationships to dict format
        relationship_dicts = [rel.model_dump(mode="json") for rel in relationships]
        
        return RelationshipListResponse(
            relationships=relationship_dicts,
            total=len(relationship_dicts),
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Error searching relationships: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SEARCH_ERROR",
                    "message": "An error occurred while searching relationships"
                }
            }
        )


@router.get("/{relationship_id:path}/versions", response_model=VersionListResponse)
async def get_relationship_versions(
    relationship_id: str = Path(..., description="Relationship ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of versions"),
    offset: int = Query(0, ge=0, description="Number of versions to skip"),
    search_service: SearchService = Depends(get_search_service)
):
    """Get version history for a relationship.
    
    Returns all versions for the specified relationship, sorted by version number
    in ascending order (oldest first).
    
    Args:
        relationship_id: The relationship ID to get versions for
        limit: Maximum number of versions to return
        offset: Number of versions to skip
        
    Returns:
        List of versions with snapshots
    """
    try:
        versions = await search_service.get_relationship_versions(
            relationship_id=relationship_id,
            limit=limit,
            offset=offset
        )
        
        # Convert versions to dict format
        version_dicts = [version.model_dump(mode="json") for version in versions]
        
        return VersionListResponse(
            versions=version_dicts,
            total=len(version_dicts),
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Error retrieving versions for {relationship_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "VERSION_ERROR",
                    "message": "An error occurred while retrieving versions"
                }
            }
        )
