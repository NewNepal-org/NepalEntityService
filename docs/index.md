# Nepal Entity Service Documentation

Welcome to the **Nepal Entity Service** (NES) documentation. NES is a comprehensive Python package designed to manage Nepali public entities including persons, organizations, and locations with full versioning and relationship tracking.

## What is Nepal Entity Service?

The Nepal Entity Service provides a robust foundation for civic technology applications by offering:

- **Structured Entity Management**: Manage persons, organizations, and locations with rich metadata
- **Versioning System**: Complete audit trails for all changes with author attribution
- **Relationship Tracking**: Model complex connections between entities
- **Multilingual Support**: Native support for Nepali (Devanagari) and English
- **RESTful API**: Public read-only API for accessing entity data
- **Data Maintainer Interface**: Pythonic interface for local data maintenance

## Quick Links

- [Getting Started](/getting-started) - Installation and quick start guide
- [Architecture](/architecture) - System architecture and design
- [API Reference](/api-reference) - Complete API endpoint documentation
- [Data Models](/data-models) - Entity, Relationship, and Version schemas
- [Examples](/examples) - Usage examples and code snippets
- [OpenAPI Schema](/docs) - Interactive API documentation

## Key Features

### Entity Management
Manage three types of entities with rich metadata:
- **Persons**: Politicians, public officials, and other public figures
- **Organizations**: Political parties, government bodies, NGOs
- **Locations**: Provinces, districts, municipalities, and wards

### Versioning and Audit Trails
Every change to entities and relationships is tracked with:
- Complete snapshots of previous states
- Author attribution and timestamps
- Change descriptions for transparency
- Historical state retrieval

### Relationship System
Model complex connections between entities:
- Typed relationships (MEMBER_OF, AFFILIATED_WITH, EMPLOYED_BY, etc.)
- Temporal relationships with start and end dates
- Bidirectional relationship queries
- Relationship versioning

### Multilingual Support
Built for Nepal's linguistic context:
- Nepali (Devanagari) and English name support
- Transliteration and romanization
- Cross-language search capabilities
- Cultural context preservation

## API Overview

The Nepal Entity Service provides a public read-only API for accessing entity data:

```
GET /api/entities              # Search and list entities
GET /api/entities/{id}         # Get specific entity
GET /api/relationships         # Query relationships
GET /api/entities/{id}/versions # Get version history
GET /api/schemas               # Discover entity types
GET /api/health                # Health check
```

All API endpoints are documented in the [API Reference](/api-reference) and available interactively at [/docs](/docs).

## Use Cases

The Nepal Entity Service is designed for:

- **Civic Technology Applications**: Build transparency and accountability platforms
- **Research and Analysis**: Analyze political and organizational networks
- **Data Journalism**: Track relationships and changes over time
- **Government Transparency**: Provide public access to entity information
- **Academic Research**: Study Nepal's political and administrative structures

## Getting Started

Ready to start using the Nepal Entity Service? Check out the [Getting Started](/getting-started) guide for installation instructions and your first API calls.

## Project Status

Nepal Entity Service v2 is currently in active development. The API is read-only and designed for public access without authentication. Data maintenance is performed through a local Pythonic interface by trusted maintainers.

## License and Contributing

This project is open source and welcomes contributions. For more information about contributing, please see our GitHub repository.

---

**Need Help?** Check out our [Examples](/examples) page for common usage patterns, or explore the [API Reference](/api-reference) for detailed endpoint documentation.
