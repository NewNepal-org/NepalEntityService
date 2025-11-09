# Nepal Entity Service Documentation

Welcome to the **Nepal Entity Service** (NES) documentation. NES is a comprehensive Python package designed to manage Nepali public entities including persons, organizations, and locations with full versioning and relationship tracking.

## Documentation Index

### For API Consumers
Start here if you want to use the public Nepal Entity Service API:

- **[API Consumer Guide](/api-guide)** - Using the public API at https://nes.newnepal.org/api
- **[OpenAPI Documentation](https://nes.newnepal.org/docs)** - Interactive API reference
- **[Data Models](/data-models)** - Understanding entity and relationship schemas
- **[Examples](/examples)** - Common usage patterns and code examples

### For Contributors
Start here if you want to contribute to the project or run your own instance:

- **[Contributor Guide](/contributor-guide)** - Setup, development workflow, and contributing
- **[Database Setup](/database-setup)** - Git submodule and database configuration
- **[Usage Examples](/usage-examples)** - Code examples, notebooks, and learning paths
- **[Service Design](/specs/nepal-entity-service/design)** - System architecture and design

### Data Maintenance & Migrations
For maintainers who manage data and migrations:

- **[Data Maintainer Guide](/data-maintainer-guide)** - Local data maintenance with Publication Service
- **[Migration Contributor Guide](/migration-contributor-guide)** - Creating and submitting data migrations
- **[Migration Maintainer Guide](/migration-maintainer-guide)** - Reviewing and executing migrations
- **[Migration Architecture](/migration-architecture)** - Migration system design and workflow

### Specifications
Technical specifications and design documents:

#### Nepal Entity Service
- [Requirements](/specs/nepal-entity-service/requirements)
- [Design](/specs/nepal-entity-service/design)
- [Tasks](/specs/nepal-entity-service/tasks)

#### Open Database Updates
- [Requirements](/specs/open-database-updates/requirements)
- [Design](/specs/open-database-updates/design)
- [Tasks](/specs/open-database-updates/tasks)

### All Documentation Files
- [api-guide.md](/api-guide) - API consumer guide
- [contributor-guide.md](/contributor-guide) - Contributor setup and workflow
- [data-maintainer-guide.md](/data-maintainer-guide) - Data maintenance guide
- [data-models.md](/data-models) - Entity schemas
- [database-setup.md](/database-setup) - Database configuration
- [examples.md](/examples) - Usage examples
- [migration-architecture.md](/migration-architecture) - Migration system design
- [migration-contributor-guide.md](/migration-contributor-guide) - Creating migrations
- [migration-maintainer-guide.md](/migration-maintainer-guide) - Executing migrations
- [usage-examples.md](/usage-examples) - Code examples and notebooks

## What is Nepal Entity Service?

The Nepal Entity Service provides a robust foundation for civic technology applications by offering:

- **Structured Entity Management**: Manage persons, organizations, and locations with rich metadata
- **Versioning System**: Complete audit trails for all changes with author attribution
- **Relationship Tracking**: Model complex connections between entities
- **Multilingual Support**: Native support for Nepali (Devanagari) and English
- **RESTful API**: Public read-only API for accessing entity data
- **Data Maintainer Interface**: Pythonic interface for local data maintenance

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

All API endpoints are documented in the interactive [OpenAPI documentation](/docs).

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

**Need Help?** Check out our [Examples](/examples) page for common usage patterns, or explore the [OpenAPI documentation](/docs) for detailed endpoint documentation.
