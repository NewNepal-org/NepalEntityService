# Search Service Guide

This guide covers the Search Service, which provides read-optimized search capabilities for querying entities, relationships, and version history.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Service API](#service-api)
4. [CLI Commands](#cli-commands)
5. [Common Use Cases](#common-use-cases)
6. [Query Patterns](#query-patterns)
7. [Best Practices](#best-practices)

---

## Overview

The Search Service provides:

- **Entity Search**: Text search with multilingual support (Nepali and English)
- **Type Filtering**: Filter by entity type and subtype
- **Attribute Filtering**: Query by entity attributes with AND logic
- **Relationship Search**: Find relationships with temporal filtering
- **Version Retrieval**: Access historical versions of entities and relationships
- **Pagination**: Efficient pagination for large result sets

### Key Features

- **Read-Only**: Focused on query operations, no write access
- **Multilingual**: Searches both Nepali (Devanagari) and English names
- **Flexible Filtering**: Combine multiple filters for precise queries
- **Temporal Queries**: Find relationships active on specific dates
- **Performance Optimized**: Efficient queries for large databases

---

## Getting Started

### Installation

```bash
pip install nepal-entity-service
```

### Basic Usage

```python
from nes.database.file_database import FileDatabase
from nes.services.search import SearchService

# Initialize database and service
db = FileDatabase(base_path="nes-db/v2")
search = SearchService(database=db)

# Search for entities
results = await search.search_entities(
    query="ram",
    entity_type="person"
)

for entity in results:
    print(f"{entity.names[0].en.full} ({entity.id})")
```

---

## Service API

### Initialization

```python
from nes.database.file_database import FileDatabase
from nes.services.search import SearchService

# Initialize with database
db = FileDatabase(base_path="nes-db/v2")
search = SearchService(database=db)
```

### Search Entities

Search entities with text query and filters:

```python
# Basic text search
results = await search.search_entities(query="ram")

# Search with type filter
results = await search.search_entities(
    query="poudel",
    entity_type="person"
)

# Search with subtype filter
results = await search.search_entities(
    query="congress",
    entity_type="organization",
    sub_type="political_party"
)

# Search with attribute filter
results = await search.search_entities(
    attributes={"party": "nepali-congress"}
)

# Combine filters
results = await search.search_entities(
    query="minister",
    entity_type="person",
    sub_type="politician",
    attributes={"party": "nepali-congress"}
)

# Paginated search
page1 = await search.search_entities(
    query="politician",
    limit=20,
    offset=0
)
page2 = await search.search_entities(
    query="politician",
    limit=20,
    offset=20
)
```

**Parameters**:
- `query` (str, optional): Text to search in entity names
- `entity_type` (str, optional): Filter by type (person, organization, location)
- `sub_type` (str, optional): Filter by subtype
- `attributes` (dict, optional): Filter by attributes (AND logic)
- `limit` (int): Maximum results (default: 100)
- `offset` (int): Skip N results (default: 0)

**Returns**: List of `Entity` objects

### Search Relationships

Search relationships with filters and temporal queries:

```python
# Search by relationship type
results = await search.search_relationships(
    relationship_type="MEMBER_OF"
)

# Search by source entity
results = await search.search_relationships(
    source_entity_id="entity:person/ram-chandra-poudel"
)

# Search by target entity
results = await search.search_relationships(
    target_entity_id="entity:organization/political_party/nepali-congress"
)

# Search for currently active relationships
results = await search.search_relationships(
    source_entity_id="entity:person/ram-chandra-poudel",
    currently_active=True
)

# Search for relationships active on a specific date
from datetime import date

results = await search.search_relationships(
    source_entity_id="entity:person/ram-chandra-poudel",
    active_on=date(2021, 6, 1)
)

# Combine filters
results = await search.search_relationships(
    relationship_type="MEMBER_OF",
    source_entity_id="entity:person/ram-chandra-poudel",
    currently_active=True
)
```

**Parameters**:
- `relationship_type` (str, optional): Filter by type (MEMBER_OF, HELD_POSITION, etc.)
- `source_entity_id` (str, optional): Filter by source entity
- `target_entity_id` (str, optional): Filter by target entity
- `active_on` (date, optional): Filter for relationships active on date
- `currently_active` (bool, optional): Filter for relationships with no end date
- `limit` (int): Maximum results (default: 100)
- `offset` (int): Skip N results (default: 0)

**Returns**: List of `Relationship` objects

### Get Entity by ID

Retrieve a specific entity:

```python
entity = await search.get_entity("entity:person/ram-chandra-poudel")

if entity:
    print(f"Name: {entity.names[0].en.full}")
    print(f"Type: {entity.type}/{entity.sub_type}")
    print(f"Attributes: {entity.attributes}")
else:
    print("Entity not found")
```

**Parameters**:
- `entity_id` (str): The entity ID

**Returns**: `Entity` object or `None`

### Get Relationship by ID

Retrieve a specific relationship:

```python
relationship = await search.get_relationship("relationship:abc123")

if relationship:
    print(f"Type: {relationship.relationship_type}")
    print(f"Source: {relationship.source_entity_id}")
    print(f"Target: {relationship.target_entity_id}")
```

**Parameters**:
- `relationship_id` (str): The relationship ID

**Returns**: `Relationship` object or `None`

### Get Entity Versions

Retrieve version history for an entity:

```python
versions = await search.get_entity_versions(
    "entity:person/ram-chandra-poudel"
)

for version in versions:
    print(f"Version {version.version_number}")
    print(f"  Created: {version.created_at}")
    print(f"  Author: {version.author.slug}")
    print(f"  Description: {version.change_description}")
```

**Parameters**:
- `entity_id` (str): The entity ID

**Returns**: List of `Version` objects

### Get Relationship Versions

Retrieve version history for a relationship:

```python
versions = await search.get_relationship_versions("relationship:abc123")

for version in versions:
    print(f"Version {version.version_number}")
    print(f"  Created: {version.created_at}")
    print(f"  Changes: {version.change_description}")
```

**Parameters**:
- `relationship_id` (str): The relationship ID

**Returns**: List of `Version` objects

### Find Entity by Name

Find entity by exact or partial name match:

```python
# Find by full name
entity = await search.find_entity_by_name(
    name="Ram Chandra Poudel",
    entity_type="person"
)

# Find by partial name
entity = await search.find_entity_by_name(
    name="Poudel",
    entity_type="person"
)

if entity:
    print(f"Found: {entity.id}")
```

**Parameters**:
- `name` (str): Name to search for
- `entity_type` (str, optional): Filter by type

**Returns**: First matching `Entity` or `None`

---

## CLI Commands

### Search Entities

```bash
# Basic search
nes search entities "ram"

# Search with type filter
nes search entities "poudel" --type person

# Search with subtype filter
nes search entities "congress" --type organization --subtype political_party

# Search with attribute filter
nes search entities --attributes party=nepali-congress

# Paginated search
nes search entities "politician" --limit 20 --offset 0

# Output as JSON
nes search entities "ram" --format json
```

### Search Relationships

```bash
# Search by type
nes search relationships --type MEMBER_OF

# Search by source entity
nes search relationships --source entity:person/ram-chandra-poudel

# Search by target entity
nes search relationships --target entity:organization/political_party/nepali-congress

# Search currently active
nes search relationships --source entity:person/ram-chandra-poudel --active

# Search active on date
nes search relationships --source entity:person/ram-chandra-poudel --active-on 2021-06-01
```

### Get Entity

```bash
# Get entity by ID
nes get entity entity:person/ram-chandra-poudel

# Output as JSON
nes get entity entity:person/ram-chandra-poudel --format json

# Include relationships
nes get entity entity:person/ram-chandra-poudel --include-relationships
```

### Get Versions

```bash
# Get entity versions
nes get versions entity:person/ram-chandra-poudel

# Get relationship versions
nes get versions relationship:abc123

# Output as JSON
nes get versions entity:person/ram-chandra-poudel --format json
```

---

## Common Use Cases

### Use Case 1: Find All Politicians from a Party

```python
async def find_party_members(party_slug: str):
    """Find all politicians from a specific party."""
    
    # Search for entities with party attribute
    results = await search.search_entities(
        entity_type="person",
        sub_type="politician",
        attributes={"party": party_slug}
    )
    
    print(f"Found {len(results)} members of {party_slug}")
    
    for entity in results:
        print(f"  - {entity.names[0].en.full}")
    
    return results

# Usage
members = await find_party_members("nepali-congress")
```

### Use Case 2: Find Current Government Ministers

```python
async def find_current_ministers():
    """Find all current government ministers."""
    
    # Search for HOLDS_POSITION relationships that are currently active
    relationships = await search.search_relationships(
        relationship_type="HOLDS_POSITION",
        currently_active=True
    )
    
    ministers = []
    for rel in relationships:
        # Get the person entity
        person = await search.get_entity(rel.source_entity_id)
        if person:
            ministers.append({
                "name": person.names[0].en.full,
                "position": rel.attributes.get("position", "Unknown"),
                "since": rel.start_date
            })
    
    return ministers

# Usage
ministers = await find_current_ministers()
for minister in ministers:
    print(f"{minister['name']}: {minister['position']} (since {minister['since']})")
```

### Use Case 3: Track Entity Changes Over Time

```python
async def track_entity_changes(entity_id: str):
    """Track all changes to an entity over time."""
    
    versions = await search.get_entity_versions(entity_id)
    
    print(f"Change history for {entity_id}:")
    print(f"Total versions: {len(versions)}\n")
    
    for version in versions:
        print(f"Version {version.version_number}")
        print(f"  Date: {version.created_at}")
        print(f"  Author: {version.author.slug}")
        print(f"  Changes: {version.change_description}")
        print()
    
    return versions

# Usage
history = await track_entity_changes("entity:person/ram-chandra-poudel")
```

### Use Case 4: Find Entities by Multiple Criteria

```python
async def find_entities_advanced(
    query: str,
    entity_type: str,
    attributes: dict,
    limit: int = 100
):
    """Advanced entity search with multiple criteria."""
    
    results = await search.search_entities(
        query=query,
        entity_type=entity_type,
        attributes=attributes,
        limit=limit
    )
    
    # Further filter results in Python if needed
    filtered = []
    for entity in results:
        # Custom filtering logic
        if entity.attributes.get("verified"):
            filtered.append(entity)
    
    return filtered

# Usage
results = await find_entities_advanced(
    query="minister",
    entity_type="person",
    attributes={"party": "nepali-congress"},
    limit=50
)
```

### Use Case 5: Build Entity Network

```python
async def build_entity_network(entity_id: str, depth: int = 1):
    """Build a network of related entities."""
    
    network = {"entities": {}, "relationships": []}
    visited = set()
    
    async def explore(current_id: str, current_depth: int):
        if current_depth > depth or current_id in visited:
            return
        
        visited.add(current_id)
        
        # Get entity
        entity = await search.get_entity(current_id)
        if entity:
            network["entities"][current_id] = entity
        
        # Get relationships
        relationships = await search.search_relationships(
            source_entity_id=current_id
        )
        
        for rel in relationships:
            network["relationships"].append(rel)
            
            # Explore target entity
            if current_depth < depth:
                await explore(rel.target_entity_id, current_depth + 1)
    
    await explore(entity_id, 0)
    
    return network

# Usage
network = await build_entity_network(
    "entity:person/ram-chandra-poudel",
    depth=2
)
print(f"Network: {len(network['entities'])} entities, {len(network['relationships'])} relationships")
```

---

## Query Patterns

### Pattern 1: Fuzzy Name Search

```python
# Search for entities with similar names
async def fuzzy_name_search(name: str):
    # Split name into parts
    parts = name.lower().split()
    
    results = []
    for part in parts:
        entities = await search.search_entities(query=part)
        results.extend(entities)
    
    # Remove duplicates
    unique = {e.id: e for e in results}
    return list(unique.values())
```

### Pattern 2: Temporal Relationship Query

```python
# Find who held a position during a specific period
async def who_held_position_during(
    position: str,
    start_date: date,
    end_date: date
):
    results = []
    
    # Check each date in range
    current = start_date
    while current <= end_date:
        rels = await search.search_relationships(
            relationship_type="HOLDS_POSITION",
            active_on=current
        )
        
        for rel in rels:
            if rel.attributes.get("position") == position:
                results.append(rel)
        
        # Move to next month
        current = current.replace(month=current.month + 1)
    
    return results
```

### Pattern 3: Hierarchical Entity Query

```python
# Find all entities in a hierarchy
async def find_hierarchy(root_id: str):
    hierarchy = []
    
    # Find all PART_OF relationships
    rels = await search.search_relationships(
        target_entity_id=root_id,
        relationship_type="PART_OF"
    )
    
    for rel in rels:
        child = await search.get_entity(rel.source_entity_id)
        if child:
            hierarchy.append(child)
            
            # Recursively find children
            sub_hierarchy = await find_hierarchy(child.id)
            hierarchy.extend(sub_hierarchy)
    
    return hierarchy
```

### Pattern 4: Attribute-Based Filtering

```python
# Complex attribute filtering
async def filter_by_attributes(
    entity_type: str,
    required_attrs: dict,
    optional_attrs: dict = None
):
    # Search with required attributes
    results = await search.search_entities(
        entity_type=entity_type,
        attributes=required_attrs
    )
    
    # Filter by optional attributes in Python
    if optional_attrs:
        filtered = []
        for entity in results:
            matches = any(
                entity.attributes.get(k) == v
                for k, v in optional_attrs.items()
            )
            if matches:
                filtered.append(entity)
        return filtered
    
    return results
```

---

## Best Practices

### 1. Use Specific Filters

```python
# Good: Specific filters reduce result set
results = await search.search_entities(
    query="ram",
    entity_type="person",
    sub_type="politician"
)

# Avoid: Too broad, returns many results
results = await search.search_entities(query="ram")
```

### 2. Paginate Large Result Sets

```python
# Good: Paginate for large queries
page_size = 50
offset = 0

while True:
    results = await search.search_entities(
        entity_type="person",
        limit=page_size,
        offset=offset
    )
    
    if not results:
        break
    
    # Process results
    for entity in results:
        process(entity)
    
    offset += page_size
```

### 3. Cache Frequently Accessed Entities

```python
# Simple cache
entity_cache = {}

async def get_entity_cached(entity_id: str):
    if entity_id not in entity_cache:
        entity_cache[entity_id] = await search.get_entity(entity_id)
    return entity_cache[entity_id]
```

### 4. Use Temporal Queries Efficiently

```python
# Good: Single query for current state
current_rels = await search.search_relationships(
    source_entity_id=entity_id,
    currently_active=True
)

# Avoid: Multiple queries for date range
# (unless you need the full history)
```

### 5. Handle Missing Entities

```python
entity = await search.get_entity(entity_id)

if entity is None:
    print(f"Entity not found: {entity_id}")
    return None

# Continue processing
```

### 6. Combine Filters for Precision

```python
# Combine multiple filters for precise results
results = await search.search_entities(
    query="minister",
    entity_type="person",
    sub_type="politician",
    attributes={
        "party": "nepali-congress",
        "verified": True
    }
)
```

---

## Additional Resources

- [Data Models](data-models.md) - Entity and relationship schemas
- [API Guide](api-guide.md) - REST API documentation
- [Publication Service Guide](publication-service-guide.md) - Creating and updating entities

---

**Last Updated:** 2024  
**Version:** 2.0
