"""Health check endpoint for nes2 API.

This module provides a health check endpoint for monitoring:
- GET /api/health - Get API health status
"""

import logging
from datetime import datetime, UTC
from fastapi import APIRouter, Depends

from nes2.database.entity_database import EntityDatabase
from nes2.api.app import get_database
from nes2.api.responses import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(database: EntityDatabase = Depends(get_database)):
    """Health check endpoint.
    
    Returns the current health status of the API and its dependencies,
    including database connectivity and version information.
    
    Returns:
        Health status information including:
        - Overall status (healthy/unhealthy)
        - API version
        - Database connectivity status
        - Timestamp
    """
    # Check database connectivity
    db_status = "connected"
    try:
        # Try to list entities to verify database is accessible
        await database.list_entities(limit=1)
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        db_status = "disconnected"
    
    # Determine overall status
    overall_status = "healthy" if db_status == "connected" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version="2.0.0",
        api_version="v2",
        database={
            "status": db_status,
            "type": "file_database"
        },
        timestamp=datetime.now(UTC)
    )
