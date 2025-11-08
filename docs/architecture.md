# Architecture

The Nepal Entity Service follows a modular architecture with clear separation of concerns. This document provides an overview of the system design, components, and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│         (Web Apps, CLI Tools, Jupyter Notebooks)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│                    (FastAPI Service)                         │
│  • Documentation Hosting (/, /getting-started, etc.)        │
│  • API Endpoints (/api/*)                                   │
│  • OpenAPI Schema (/docs)                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Search Service   │  │Publication Service│                │
│  │ (Read-Optimized) │  │ (Write Operations)│                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│              (File-Based JSON Storage)                       │
│                    nes-db/v2/                                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer

The API layer is built with FastAPI and provides:

- **Documentation Hosting**: Serves Markdown documentation at root endpoints
- **RESTful API**: JSON API under `/api` prefix
- **OpenAPI Schema**: Interactive documentation at `/docs`
- **CORS Support**: Cross-origin requests for web applications
- **Error Handling**: Standardized error responses

**Key Features**:
- Automatic request validation using Pydantic
- Async/await for high performance
- Dependency injection for services
- Comprehensive error handling

### 2. Service Layer

The service layer implements business logic and is divided into specialized services:

#### Search Service (Read-Optimized)

Provides read-only access to entity data:
- Entity search with text queries
- Type and subtype filtering
- Attribute-based filtering
- Relationship queries
- Version history retrieval
- Pagination support

**Design Philosophy**: Optimized for fast reads with simple, database-backed queries.

#### Publication Service (Write Operations)

Manages entity lifecycle and data maintenance:
- Entity creation and updates
- Relationship management
- Automatic versioning
- Author attribution
- Coordinated operations
- Business rule enforcement

**Design Philosophy**: Ensures data integrity through coordinated modules and automatic versioning.

#### Scraping Service (Data Extraction)

Extracts and normalizes data from external sources:
- Wikipedia extraction
- Multi-source web scraping
- LLM-powered normalization
- Translation (Nepali ↔ English)
- Relationship discovery

**Design Philosophy**: Standalone service that returns normalized data without database access.

### 3. Database Layer

The database layer provides persistent storage:

#### EntityDatabase (Abstract Interface)

Defines standard operations:
- Entity CRUD operations
- Relationship management
- Version storage and retrieval
- Author tracking

#### FileDatabase (Implementation)

File-based storage using JSON:
- Human-readable entity files
- Directory structure by type/subtype
- Atomic file operations
- Version history preservation

**Storage Location**: `nes-db/v2/`

**Directory Structure**:
```
nes-db/v2/
├── entity/
│   ├── person/
│   │   └── ram-chandra-poudel.json
│   ├── organization/
│   │   └── political_party/
│   │       └── nepali-congress.json
│   └── location/
│       └── province/
│           └── bagmati.json
├── relationship/
│   └── {relationship-id}.json
├── version/
│   └── entity/
│       └── person/
│           └── ram-chandra-poudel/
│               ├── v1.json
│               └── v2.json
└── actor/
    └── {actor-id}.json
```

## Data Flow

### Read Operations (Search)

```
Client Request
    ↓
API Endpoint (/api/entities)
    ↓
Search Service
    ↓
FileDatabase
    ↓
JSON Files
    ↓
Response to Client
```

### Write Operations (Publication)

```
Data Maintainer (Local)
    ↓
Publication Service
    ↓
Entity/Relationship/Version Modules
    ↓
FileDatabase
    ↓
JSON Files + Version Snapshots
```

### External Data Import

```
External Source (Wikipedia, etc.)
    ↓
Scraping Service
    ↓
Normalized Data
    ↓
Data Maintainer Review
    ↓
Publication Service
    ↓
Database
```

## Key Design Decisions

### 1. Read-Only Public API

**Decision**: The public API is read-only. Write operations are performed locally by trusted maintainers.

**Rationale**:
- Simplifies security (no authentication needed)
- Ensures data quality through human review
- Reduces complexity of public API
- Allows careful curation of public data

### 2. File-Based Storage

**Decision**: Use JSON files instead of a traditional database.

**Rationale**:
- Human-readable and Git-friendly
- Simple backup and version control
- No database server required
- Easy to inspect and debug
- Sufficient performance for read-heavy workload

### 3. Service Separation

**Decision**: Separate Search, Publication, and Scraping services.

**Rationale**:
- Clear separation of concerns
- Independent optimization (read vs. write)
- Easier testing and maintenance
- Flexible deployment options

### 4. Automatic Versioning

**Decision**: All entity and relationship changes create version snapshots automatically.

**Rationale**:
- Complete audit trail
- Historical state retrieval
- Transparency and accountability
- No manual version management

### 5. Multilingual First

**Decision**: Native support for Nepali and English from the ground up.

**Rationale**:
- Reflects Nepal's linguistic reality
- Better search and discovery
- Cultural context preservation
- Accessibility for all users

## Performance Considerations

### Read Optimization

- **Caching**: In-memory cache with TTL for frequently accessed entities
- **Batch Operations**: Efficient bulk reads
- **Index Files**: Pre-computed indexes for common queries
- **Async I/O**: Non-blocking file operations

### Write Optimization

- **Deferred Indexing**: Update indexes during write operations
- **Atomic Operations**: Safe concurrent access
- **Validation First**: Catch errors before file writes

## Security

### API Security

- **CORS**: Configured for cross-origin requests
- **Rate Limiting**: Prevents abuse (100 req/min per IP)
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: No sensitive information in error messages

### Data Security

- **Read-Only API**: No public write access
- **Local Maintenance**: Write operations require local file system access
- **Version Control**: Git tracks all changes to data files
- **Backup**: Version history provides automatic backup

## Scalability

### Current Scale

- **Entities**: Optimized for 10,000+ entities
- **Relationships**: Efficient for 50,000+ relationships
- **Versions**: Handles millions of version snapshots
- **API Requests**: 100+ requests/second

### Future Scaling

If needed, the architecture supports:
- Database migration (PostgreSQL, MongoDB)
- Caching layer (Redis)
- Search engine (Elasticsearch)
- CDN for static documentation
- Horizontal API scaling

## Technology Stack

- **API Framework**: FastAPI (Python 3.11+)
- **Data Validation**: Pydantic v2
- **Storage**: JSON files
- **Documentation**: Markdown + Python-Markdown
- **Testing**: pytest + pytest-asyncio
- **Package Management**: Poetry

## Next Steps

- [Data Models](/data-models) - Understanding entity schemas
- [API Reference](/api-reference) - Complete endpoint documentation
- [Examples](/examples) - Usage examples and patterns
