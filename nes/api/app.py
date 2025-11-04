"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import entities, relationships, schemas, versions

app = FastAPI(
    title="NepalEntityService API",
    description="The Nepal Entity Service API loads the entity database (person, organizations, govt. bodies, etc.) and exposes endpoints for search, lookup, versions, and relationships. This will live in the public domain.",
    version="0.1.3",
    contact={
        "url": "https://newnepal.org",
        "name": "NewNepal.org",
        "email": "hello@newnepal.org",
        "something": "efgh",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["HEAD", "GET"],
)

app.include_router(schemas.router)
app.include_router(entities.router)
app.include_router(versions.router)
app.include_router(relationships.router)
