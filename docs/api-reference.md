# API Reference

Complete reference for all Nepal Entity Service API endpoints. All endpoints are read-only and return JSON responses.

**Base URL**: `http://localhost:8000` (or your deployment URL)

## Authentication

The public API does not require authentication. All endpoints are publicly accessible.

## Rate Limiting

- **100 requests per minute** per IP address
- **1000 requests per hour** per IP address

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

## Common Parameters

### Pagination

All list endpoints support pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Maximum number of results (1-100) |
| `offset` | integer | 0 | Number of results to skip |

### Response Format

All list endpoints return:

```json
{
  "entities": [...],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

## Endpoints

### Entities

#### List/Search Entities

```
GET /api/entities
```

Search and filter entities with various criteria.

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Text search across entity names (Nepali and English) |
| `entity_type` | string | Filter by type: `person`, `organization`, `location` |
| `sub_type` | string | Filter by subtype (e.g., `political_party`, `district`) |
| `attributes` | JSON string | Filter by attributes (e.g., `{"party":"nepali-congress"}`) |
| `limit` | integer | Maximum results (default: 10, max: 100) |
| `offset` | integer | Results to skip (default: 0) |

**Example Request**:

```bash
curl "http://localhost:8000/api/entities?query=poudel&entity_type=person&limit=5"
```

**Example Response**:

```json
{
  "entities": [
    {
      "id": "entity:person/ram-chandra-poudel",
      "slug": "ram-chandra-poudel",
      "type": "person",
      "names": [
        {
          "kind": "PRIMARY",
          "en": {
            "full": "Ram Chandra Poudel",
            "first": "Ram Chandra",
            "last": "Poudel"
          },
          "ne": {
            "full": "राम चन्द्र पौडेल"
          }
        }
      ],
      "version_summary": {
        "version": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "created_by": "actor:system:importer"
      },
      "attributes": {
        "party": "nepali-congress",
        "position": "president"
      }
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}
```

#### Get Entity by ID

```
GET /api/entities/{entity_id}
```

Retrieve a specific entity by its ID.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Full entity ID (e.g., `entity:person/ram-chandra-poudel`) |

**Example Request**:

```bash
curl "http://localhost:8000/api/entities/entity:person/ram-chandra-poudel"
```

**Example Response**:

```json
{
  "id": "entity:person/ram-chandra-poudel",
  "slug": "ram-chandra-poudel",
  "type": "person",
  "names": [...],
  "version_summary": {...},
  "identifiers": [
    {
      "scheme": "wikipedia",
      "value": "Ram_Chandra_Poudel",
      "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel"
    }
  ],
  "attributes": {...},
  "contacts": [],
  "descriptions": {
    "en": {
      "value": "Nepali politician and current President of Nepal",
      "provenance": "human"
    }
  }
}
```

**Error Responses**:

- `404 Not Found`: Entity does not exist

#### Get Entity Versions

```
GET /api/entities/{entity_id}/versions
```

Retrieve version history for an entity.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Full entity ID |

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Maximum versions to return (default: 10) |
| `offset` | integer | Versions to skip (default: 0) |

**Example Request**:

```bash
curl "http://localhost:8000/api/entities/entity:person/ram-chandra-poudel/versions"
```

**Example Response**:

```json
{
  "versions": [
    {
      "entity_or_relationship_id": "entity:person/ram-chandra-poudel",
      "version_number": 2,
      "actor": "actor:human:data-maintainer",
      "created_at": "2024-01-20T14:30:00Z",
      "change_description": "Updated party affiliation",
      "snapshot": {
        "id": "entity:person/ram-chandra-poudel",
        "slug": "ram-chandra-poudel",
        ...
      }
    },
    {
      "entity_or_relationship_id": "entity:person/ram-chandra-poudel",
      "version_number": 1,
      "actor": "actor:system:importer",
      "created_at": "2024-01-15T10:30:00Z",
      "change_description": "Initial import",
      "snapshot": {...}
    }
  ],
  "total": 2,
  "limit": 10,
  "offset": 0
}
```

### Relationships

#### Get Entity Relationships

```
GET /api/entities/{entity_id}/relationships
```

Get all relationships for a specific entity.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Full entity ID |

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `relationship_type` | string | Filter by type (e.g., `MEMBER_OF`, `AFFILIATED_WITH`) |
| `currently_active` | boolean | Filter for relationships without end date |
| `limit` | integer | Maximum results (default: 10) |
| `offset` | integer | Results to skip (default: 0) |

**Example Request**:

```bash
curl "http://localhost:8000/api/entities/entity:person/ram-chandra-poudel/relationships?relationship_type=MEMBER_OF"
```

**Example Response**:

```json
{
  "relationships": [
    {
      "id": "relationship:abc123",
      "source_entity_id": "entity:person/ram-chandra-poudel",
      "target_entity_id": "entity:organization/political_party/nepali-congress",
      "type": "MEMBER_OF",
      "start_date": "2000-01-01",
      "end_date": null,
      "attributes": {
        "role": "senior-leader"
      },
      "version_summary": {
        "version": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "created_by": "actor:system:importer"
      }
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### Search Relationships

```
GET /api/relationships
```

Search relationships across all entities.

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `relationship_type` | string | Filter by relationship type |
| `source_entity_id` | string | Filter by source entity |
| `target_entity_id` | string | Filter by target entity |
| `currently_active` | boolean | Filter for active relationships |
| `limit` | integer | Maximum results (default: 10) |
| `offset` | integer | Results to skip (default: 0) |

**Example Request**:

```bash
curl "http://localhost:8000/api/relationships?target_entity_id=entity:organization/political_party/nepali-congress"
```

#### Get Relationship Versions

```
GET /api/relationships/{relationship_id}/versions
```

Retrieve version history for a relationship.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `relationship_id` | string | Relationship ID |

**Query Parameters**: Same as entity versions

### Schemas

#### Get Entity Type Schemas

```
GET /api/schemas
```

Discover available entity types and subtypes.

**Example Request**:

```bash
curl "http://localhost:8000/api/schemas"
```

**Example Response**:

```json
{
  "entity_types": {
    "person": {
      "description": "Individual persons",
      "subtypes": []
    },
    "organization": {
      "description": "Organizations and institutions",
      "subtypes": [
        "political_party",
        "government_body",
        "ngo"
      ]
    },
    "location": {
      "description": "Geographic locations",
      "subtypes": [
        "province",
        "district",
        "metropolitan_city",
        "municipality",
        "rural_municipality",
        "ward"
      ]
    }
  }
}
```

#### Get Relationship Type Schemas

```
GET /api/schemas/relationships
```

Discover available relationship types.

**Example Response**:

```json
{
  "relationship_types": [
    "MEMBER_OF",
    "AFFILIATED_WITH",
    "EMPLOYED_BY",
    "REPRESENTS",
    "LOCATED_IN",
    "PART_OF"
  ]
}
```

### Health Check

#### Get API Health Status

```
GET /api/health
```

Check API and database health.

**Example Request**:

```bash
curl "http://localhost:8000/api/health"
```

**Example Response**:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "api_version": "v2",
  "database": {
    "status": "connected",
    "type": "FileDatabase",
    "path": "./nes-db/v2"
  },
  "timestamp": "2024-01-20T15:45:30Z"
}
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "field_name",
        "message": "Field-specific error"
      }
    ]
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Entity or resource not found |
| `INVALID_REQUEST` | 400 | Malformed request |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Examples

### Search for Politicians

```bash
curl "http://localhost:8000/api/entities?entity_type=person&attributes={\"occupation\":\"politician\"}"
```

### Find All Members of a Party

```bash
curl "http://localhost:8000/api/relationships?relationship_type=MEMBER_OF&target_entity_id=entity:organization/political_party/nepali-congress"
```

### Get Entity with Version History

```bash
# Get current entity
curl "http://localhost:8000/api/entities/entity:person/ram-chandra-poudel"

# Get version history
curl "http://localhost:8000/api/entities/entity:person/ram-chandra-poudel/versions"
```

### Paginate Through Results

```bash
# Page 1
curl "http://localhost:8000/api/entities?limit=20&offset=0"

# Page 2
curl "http://localhost:8000/api/entities?limit=20&offset=20"

# Page 3
curl "http://localhost:8000/api/entities?limit=20&offset=40"
```

## Interactive Documentation

For interactive API exploration, visit the [OpenAPI documentation](/docs) which provides:

- Try-it-out functionality for all endpoints
- Request/response examples
- Schema documentation
- Authentication testing (when applicable)

## Need Help?

- Check the [Examples](/examples) page for more usage patterns
- Review [Data Models](/data-models) to understand entity schemas
- Visit [Getting Started](/getting-started) for basic usage
