"""API module for nes2.

This module provides the FastAPI application for the Nepal Entity Service v2.
The API serves read-only endpoints for entity, relationship, and version data.
"""

from .app import app

__all__ = ["app"]
