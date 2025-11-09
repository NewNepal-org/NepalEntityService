# API Consumer Guide

This guide is for developers who want to consume the Nepal Entity Service public API to build applications, conduct research, or explore Nepal's political landscape.

## Overview

The Nepal Entity Service provides a public, read-only RESTful API for accessing structured data about Nepali public entities including politicians, political parties, government organizations, and administrative locations.

**Public API Base URL**: `https://nes.newnepal.org/api`

## Key Concepts

### Entities

Entities are the core data objects in NES. There are three types:

- **Persons**: Politicians, public officials, and other public figures
- **Organizations**: Political parties, government bodies, NGOs
- **Locations**: Provinces, districts, municipalities, and wards

Each entity has:
- **Unique ID**: Hierarchical identifier (e.g., `entity:person/ram-chandra-poudel`)
- **Names**: Multilingual support (English and Nepali/Devanagari)
- **Attributes**: Type-specific metadata
- **Version History**: Complete audit trail of all changes

### Relationships

Relationships connect entities together:
- **MEMBER_OF**: Person → Organization (party membership)
- **AFFILIATED_WITH**: Person → Organization (affiliations)
- **EMPLOYED_BY**: Person → Organization (employment)
- **LOCATED_IN**: Entity → Location (geographic location)

Relationships can have temporal bounds (start/end dates) and their own version history.

### Versioning

Every change to entities and relationships is tracked:
- Complete snapshots of previous states
- Author attribution and timestamps
- Change descriptions for transparency
- Historical state retrieval

## Architecture

The API follows a layered architecture:

```
Client Application
       ↓
  FastAPI Service (https://nes.newnepal.org/api)
       ↓
  Search Service (Read-Optimized)
       ↓
  File-Based Database (Git-backed)
```

For detailed architecture, see the [Service Design](/specs/nepal-entity-service/design).

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/entities` | GET | Search and list entities |
| `/api/entities/{id}` | GET | Get specific entity |
| `/api/entities/{id}/relationships` | GET | Get entity relationships |
| `/api/entities/{id}/versions` | GET | Get version history |
| `/api/relationships` | GET | Query relationships |
| `/api/schemas` | GET | Discover entity types |
| `/api/health` | GET | Health check |

### Interactive Documentation

Visit the [OpenAPI documentation](https://nes.newnepal.org/docs) for:
- Complete endpoint reference
- Request/response schemas
- Interactive API testing
- Example requests

## Your First API Call

### Using cURL

```bash
curl "https://nes.newnepal.org/api/entities?query=poudel"
```

### Using Python

```python
import requests

response = requests.get(
    "https://nes.newnepal.org/api/entities",
    params={"query": "poudel"}
)

data = response.json()
print(f"Found {data['total']} entities")

for entity in data['entities']:
    print(f"- {entity['names'][0]['en']['full']}")
```

### Using JavaScript

```javascript
fetch('https://nes.newnepal.org/api/entities?query=poudel')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.total} entities`);
    data.entities.forEach(entity => {
      console.log(`- ${entity.names[0].en.full}`);
    });
  });
```

## Common Operations

### Search for Entities

Search supports both English and Nepali:

```bash
# Search by English name
curl "https://nes.newnepal.org/api/entities?query=ram+chandra+poudel"

# Search by Nepali name
curl "https://nes.newnepal.org/api/entities?query=राम+चन्द्र+पौडेल"
```

### Filter by Entity Type

```bash
# Get all persons
curl "https://nes.newnepal.org/api/entities?entity_type=person"

# Get all political parties
curl "https://nes.newnepal.org/api/entities?entity_type=organization&sub_type=political_party"
```

### Get a Specific Entity

```bash
curl "https://nes.newnepal.org/api/entities/entity:person/ram-chandra-poudel"
```

### Query Relationships

```bash
# Get all relationships for an entity
curl "https://nes.newnepal.org/api/entities/entity:person/ram-chandra-poudel/relationships"

# Filter by relationship type
curl "https://nes.newnepal.org/api/entities/entity:person/ram-chandra-poudel/relationships?relationship_type=MEMBER_OF"
```

### Get Version History

```bash
curl "https://nes.newnepal.org/api/entities/entity:person/ram-chandra-poudel/versions"
```

## Pagination

All list endpoints support pagination:

```bash
# Get first 10 results
curl "https://nes.newnepal.org/api/entities?limit=10&offset=0"

# Get next 10 results
curl "https://nes.newnepal.org/api/entities?limit=10&offset=10"
```

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "entities": [...],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

Error responses include detailed error information:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Entity not found"
  }
}
```

## Rate Limiting

The public API has rate limits to ensure fair usage:

- **100 requests per minute** per IP address
- **1000 requests per hour** per IP address

If you need higher limits, please contact us about dedicated access.

## CORS Support

The API supports CORS (Cross-Origin Resource Sharing), allowing you to make requests from web applications:

```javascript
// Works from any origin
fetch('https://nes.newnepal.org/api/entities')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Data Models

For detailed information about entity and relationship schemas, see the [Data Models](/data-models) documentation.

## Use Cases

The Nepal Entity Service API is designed for:

- **Civic Technology Applications**: Build transparency and accountability platforms
- **Research and Analysis**: Analyze political and organizational networks
- **Data Journalism**: Track relationships and changes over time
- **Government Transparency**: Provide public access to entity information
- **Academic Research**: Study Nepal's political and administrative structures

## Next Steps

- Explore the [Interactive OpenAPI Documentation](https://nes.newnepal.org/docs)
- Review [Data Models](/data-models) to understand entity schemas
- Check out [Examples](/examples) for common usage patterns
- Learn about the [Service Design](/specs/nepal-entity-service/design)

## Need Help?

- Check the [Examples](/examples) page for common patterns
- Review the [OpenAPI documentation](https://nes.newnepal.org/docs) for detailed endpoint reference
- Visit our [GitHub repository](https://github.com/NewNepal-org/NepalEntityService) for issues and discussions
