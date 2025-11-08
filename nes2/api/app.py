"""FastAPI application for nes2 API.

This module creates and configures the FastAPI application with:
- CORS middleware for cross-origin requests
- Error handling middleware
- Dependency injection for services
- API routes under /api prefix
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from nes2 import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Nepal Entity Service API v2")
    
    # Initialize database
    config.Config.initialize_database(base_path="./nes-db/v2")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nepal Entity Service API v2")
    config.Config.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Nepal Entity Service API",
    description="RESTful API for accessing Nepali public entity data",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# Dependency Injection
# ============================================================================

# Import dependency functions from Config class
get_database = config.Config.get_database
get_search_service = config.Config.get_search_service
get_publication_service = config.Config.get_publication_service


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors
            }
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Data validation failed",
                "details": errors
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": str(exc)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )


# ============================================================================
# Root Endpoint (will be used for documentation in future tasks)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - will serve documentation in future tasks."""
    return {
        "message": "Nepal Entity Service API v2",
        "version": "2.0.0",
        "docs": "/docs",
        "api": "/api"
    }


# ============================================================================
# API Routes
# ============================================================================

# Import and include routers
from nes2.api.routes import entities, relationships, schemas, health

app.include_router(entities.router)
app.include_router(relationships.router)
app.include_router(schemas.router)
app.include_router(health.router)
