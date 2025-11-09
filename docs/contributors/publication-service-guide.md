# Publication Service Guide

This guide covers the Publication Service, which provides write operations for creating, updating, and deleting entities and relationships with automatic versioning.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Service API](#service-api)
4. [Entity Operations](#entity-operations)
5. [Relationship Operations](#relationship-operations)
6. [Versioning](#versioning)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Publication Service provides:

- **Entity Management**: Create, update, and delete entities
- **Relationship Management**: Create, update, and delete relationships
- **Automatic Versioning**: Every change creates a new version with full audit trail
- **Author Attribution**: All changes are attributed to an author
- **Business Rules**: Enforces data integrity and validation
- **Bidirectional Consistency**: Maintains relationship consistency

### Key Features

- **Write Operations**: Focused on data modification
- **Version Control**: Complete history of all changes
- **Validation**: Ensures data quality and schema compliance
- **Atomic Operations**: Changes are applied atomically
- **Audit Trail**: Full attribution and change descriptions

---

## Getting Started

### Installation

```bash
pip install nepal-entity-service
```

### Basic Usage

```python
from nes.database.file_database import FileDatabase
from nes.services.publication import PublicationService

# Initialize database and service
db = FileDatabase(base_path="nes-db/v2")
pub_service = PublicationService(database=db)

# Create an entity
entity = await pub_service.create_entity(
    entity_data={
        "slug": "ram-chandra-poudel",
        "type": "person",
        "sub_type": "politician",
        "names": [
            {
                "kind": "PRIMARY",
                "en": {"full": "Ram Chandra Poudel"},
                "ne": {"full": "राम चन्द्र पौडेल"}
            }
        ]
    },
    author_id="author:human:data-maintainer",
    change_description="Initial import from official records"
)

print(f"Created entity: {entity.id}")
```

---

## Service API

### Initialization

```python
from nes.database.file_database import FileDatabase
from nes.services.publication import PublicationService

# Initialize with database
db = FileDatabase(base_path="nes-db/v2")
pub_service = PublicationService(database=db)
```

---

## Entity Operations

### Create Entity

Create a new entity:

```python
entity_data = {
    "slug": "ram-chandra-poudel",
    "type": "person",
    "sub_type": "politician",
    "names": [
        {
            "kind": "PRIMARY",
            "en": {"full": "Ram Chandra Poudel"},
            "ne": {"full": "राम चन्द्र पौडेल"}
        }
    ],
    "attributes": {
        "party": "nepali-congress",
        "position": "President"
    }
}

entity = await pub_service.create_entity(
    entity_data=entity_data,
    author_id="author:human:data-maintainer",
    change_description="Initial import from official records"
)

print(f"Created: {entity.id}")
print(f"Version: {entity.version}")
```

**Parameters**:
- `entity_data` (dict): Entity data following the entity schema
- `author_id` (str): ID of the author creating the entity
- `change_description` (str): Description of this change

**Returns**: Created `Entity` with version 1

**Raises**: `ValueError` if entity data is invalid or entity already exists

### Get Entity

Retrieve an entity:

```python
entity = await pub_service.get_entity("entity:person/ram-chandra-poudel")

if entity:
    print(f"Name: {entity.names[0].en.full}")
    print(f"Version: {entity.version}")
else:
    print("Entity not found")
```

**Parameters**:
- `entity_id` (str): The unique identifier of the entity

**Returns**: `Entity` object or `None`

### Update Entity

Update an existing entity:

```python
# Get the entity
entity = await pub_service.get_entity("entity:person/ram-chandra-poudel")

# Modify attributes
entity.attributes["position"] = "President of Nepal"
entity.attributes["term_start"] = "2023-03-13"

# Update with automatic versioning
updated_entity = await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Updated position to President"
)

print(f"Updated to version {updated_entity.version}")
```

**Parameters**:
- `entity` (Entity): Entity to update (with modifications)
- `author_id` (str): ID of the author updating the entity
- `change_description` (str): Description of this change

**Returns**: Updated `Entity` with incremented version number

**Raises**: `ValueError` if entity doesn't exist or update is invalid

### Delete Entity

Delete an entity:

```python
success = await pub_service.delete_entity("entity:person/ram-chandra-poudel")

if success:
    print("Entity deleted")
else:
    print("Entity not found")
```

**Parameters**:
- `entity_id` (str): The unique identifier of the entity to delete

**Returns**: `True` if deleted, `False` if entity didn't exist

**Note**: This is a hard delete. Version history is preserved but the entity is removed.

### Get Entity Versions

Retrieve version history:

```python
versions = await pub_service.get_entity_versions("entity:person/ram-chandra-poudel")

for version in versions:
    print(f"Version {version.version_number}")
    print(f"  Created: {version.created_at}")
    print(f"  Author: {version.author.slug}")
    print(f"  Description: {version.change_description}")
```

**Parameters**:
- `entity_id` (str): The unique identifier of the entity

**Returns**: List of `Version` objects, ordered by version number

---

## Relationship Operations

### Create Relationship

Create a new relationship:

```python
from datetime import date

relationship = await pub_service.create_relationship(
    source_entity_id="entity:person/ram-chandra-poudel",
    target_entity_id="entity:organization/political_party/nepali-congress",
    relationship_type="MEMBER_OF",
    start_date=date(1970, 1, 1),
    attributes={
        "role": "Senior Leader",
        "positions": ["Acting President", "General Secretary"]
    },
    author_id="author:human:data-maintainer",
    change_description="Added party membership"
)

print(f"Created relationship: {relationship.id}")
```

**Parameters**:
- `source_entity_id` (str): Source entity ID
- `target_entity_id` (str): Target entity ID
- `relationship_type` (str): Type of relationship (MEMBER_OF, HOLDS_POSITION, etc.)
- `start_date` (date, optional): When the relationship started
- `end_date` (date, optional): When the relationship ended
- `attributes` (dict, optional): Additional relationship metadata
- `author_id` (str): ID of the author creating the relationship
- `change_description` (str): Description of this change

**Returns**: Created `Relationship` with version 1

**Raises**: `ValueError` if entities don't exist or relationship is invalid

### Get Relationship

Retrieve a relationship:

```python
relationship = await pub_service.get_relationship(relationship_id)

if relationship:
    print(f"Type: {relationship.relationship_type}")
    print(f"Source: {relationship.source_entity_id}")
    print(f"Target: {relationship.target_entity_id}")
```

**Parameters**:
- `relationship_id` (str): The unique identifier of the relationship

**Returns**: `Relationship` object or `None`

### Update Relationship

Update an existing relationship:

```python
# Get the relationship
relationship = await pub_service.get_relationship(relationship_id)

# Add end date
relationship.end_date = date(2024, 7, 15)
relationship.attributes["end_reason"] = "Term completed"

# Update with versioning
updated_rel = await pub_service.update_relationship(
    relationship=relationship,
    author_id="author:human:data-maintainer",
    change_description="Added end date"
)

print(f"Updated to version {updated_rel.version}")
```

**Parameters**:
- `relationship` (Relationship): Relationship to update (with modifications)
- `author_id` (str): ID of the author updating the relationship
- `change_description` (str): Description of this change

**Returns**: Updated `Relationship` with incremented version number

### Delete Relationship

Delete a relationship:

```python
success = await pub_service.delete_relationship(relationship_id)

if success:
    print("Relationship deleted")
else:
    print("Relationship not found")
```

**Parameters**:
- `relationship_id` (str): The unique identifier of the relationship

**Returns**: `True` if deleted, `False` if relationship didn't exist

### Get Relationship Versions

Retrieve version history:

```python
versions = await pub_service.get_relationship_versions(relationship_id)

for version in versions:
    print(f"Version {version.version_number}")
    print(f"  Created: {version.created_at}")
    print(f"  Changes: {version.change_description}")
```

**Parameters**:
- `relationship_id` (str): The unique identifier of the relationship

**Returns**: List of `Version` objects for the relationship

---

## Versioning

### How Versioning Works

Every create and update operation creates a new version:

```python
# Create entity (version 1)
entity = await pub_service.create_entity(
    entity_data=data,
    author_id="author:human:maintainer",
    change_description="Initial creation"
)
print(f"Version: {entity.version}")  # 1

# Update entity (version 2)
entity.attributes["new_field"] = "value"
entity = await pub_service.update_entity(
    entity=entity,
    author_id="author:human:maintainer",
    change_description="Added new field"
)
print(f"Version: {entity.version}")  # 2

# Update again (version 3)
entity.attributes["another_field"] = "value"
entity = await pub_service.update_entity(
    entity=entity,
    author_id="author:human:maintainer",
    change_description="Added another field"
)
print(f"Version: {entity.version}")  # 3
```

### Version History

Access complete version history:

```python
versions = await pub_service.get_entity_versions(entity.id)

print(f"Total versions: {len(versions)}")

for version in versions:
    print(f"\nVersion {version.version_number}")
    print(f"  Date: {version.created_at}")
    print(f"  Author: {version.author.slug}")
    print(f"  Description: {version.change_description}")
    print(f"  Data snapshot: {version.data}")
```

### Version Metadata

Each version includes:

- **version_number**: Sequential version number (1, 2, 3, ...)
- **created_at**: Timestamp of when version was created
- **author**: Author who made the change
- **change_description**: Description of what changed
- **data**: Complete snapshot of entity/relationship at that version

---

## Best Practices

### 1. Always Provide Meaningful Change Descriptions

```python
# Good: Descriptive change description
await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Updated position after 2023 election results"
)

# Bad: Vague description
await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Update"
)
```

### 2. Use Meaningful Author IDs

```python
# Good author IDs
"author:human:john-doe"
"author:system:wikipedia-importer"
"author:migration:005-add-ministers"

# Bad author IDs
"author:user"
"author:admin"
```

### 3. Validate Before Creating

```python
def validate_entity_data(entity_data):
    """Validate entity data before creation."""
    errors = []
    
    if "slug" not in entity_data:
        errors.append("Missing slug")
    if "type" not in entity_data:
        errors.append("Missing type")
    if "names" not in entity_data or not entity_data["names"]:
        errors.append("Missing names")
    
    # Check for PRIMARY name
    has_primary = any(
        name.get("kind") == "PRIMARY" 
        for name in entity_data.get("names", [])
    )
    if not has_primary:
        errors.append("No PRIMARY name")
    
    return len(errors) == 0, errors

# Use validation
is_valid, errors = validate_entity_data(entity_data)
if not is_valid:
    print(f"Validation errors: {errors}")
else:
    entity = await pub_service.create_entity(...)
```

### 4. Handle Errors Gracefully

```python
try:
    entity = await pub_service.create_entity(
        entity_data=entity_data,
        author_id="author:human:data-maintainer",
        change_description="Import"
    )
except ValueError as e:
    print(f"Validation error: {e}")
    # Log error, skip entity, or retry with corrections
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log error and investigate
```

### 5. Check for Existence Before Creating

```python
from nes.core.identifiers import build_entity_id

# Check if entity exists
entity_id = build_entity_id("person", "politician", "ram-chandra-poudel")
existing = await pub_service.get_entity(entity_id)

if existing:
    # Update instead of create
    await pub_service.update_entity(...)
else:
    # Create new
    await pub_service.create_entity(...)
```

### 6. Verify Relationships Before Creating

```python
# Verify both entities exist
source = await pub_service.get_entity(source_id)
target = await pub_service.get_entity(target_id)

if not source:
    print(f"Source entity not found: {source_id}")
elif not target:
    print(f"Target entity not found: {target_id}")
else:
    # Create relationship
    relationship = await pub_service.create_relationship(...)
```

### 7. Use Transactions for Related Operations

```python
async def create_politician_with_party(politician_data, party_id, author_id):
    """Create politician and party membership atomically."""
    try:
        # Create politician
        politician = await pub_service.create_entity(
            entity_data=politician_data,
            author_id=author_id,
            change_description="Import politician"
        )
        
        # Create party membership
        relationship = await pub_service.create_relationship(
            source_entity_id=politician.id,
            target_entity_id=party_id,
            relationship_type="MEMBER_OF",
            author_id=author_id,
            change_description="Add party membership"
        )
        
        return politician, relationship
        
    except Exception as e:
        print(f"Failed to create politician with party: {e}")
        raise
```

### 8. Document Data Sources

```python
# Include data source in attributes
entity_data = {
    "slug": "ram-chandra-poudel",
    "type": "person",
    "attributes": {
        "party": "nepali-congress",
        "data_source": "Election Commission of Nepal",
        "source_url": "https://election.gov.np/...",
        "verified_date": "2024-01-15"
    }
}
```

---

## Troubleshooting

### Issue 1: Entity Already Exists

**Error**: `ValueError: Entity with slug 'X' and type 'Y' already exists`

**Solution**:
```python
from nes.core.identifiers import build_entity_id

entity_id = build_entity_id("person", "politician", "ram-chandra-poudel")
existing = await pub_service.get_entity(entity_id)

if existing:
    # Update instead
    await pub_service.update_entity(...)
else:
    # Create new
    await pub_service.create_entity(...)
```

### Issue 2: Missing PRIMARY Name

**Error**: `ValueError: Entity must have at least one name with kind='PRIMARY'`

**Solution**:
```python
# Ensure at least one name has kind="PRIMARY"
"names": [
    {
        "kind": "PRIMARY",  # Required
        "en": {"full": "Name"},
        "ne": {"full": "नाम"}
    }
]
```

### Issue 3: Invalid Relationship

**Error**: `ValueError: Entity X does not exist`

**Solution**:
```python
# Verify both entities exist
source = await pub_service.get_entity(source_id)
target = await pub_service.get_entity(target_id)

if not source:
    print(f"Source entity not found: {source_id}")
elif not target:
    print(f"Target entity not found: {target_id}")
else:
    # Create relationship
    relationship = await pub_service.create_relationship(...)
```

### Issue 4: Version Conflicts

**Issue**: Multiple maintainers updating the same entity

**Solution**:
```python
# Always get the latest version before updating
entity = await pub_service.get_entity(entity_id)

# Make changes
entity.attributes["position"] = "New Position"

# Update
updated = await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Update position"
)
```

### Issue 5: Invalid Entity Data

**Error**: `ValueError: Invalid entity data`

**Solution**:
```python
# Validate data structure
required_fields = ["slug", "type", "names"]
for field in required_fields:
    if field not in entity_data:
        print(f"Missing required field: {field}")

# Check names structure
if "names" in entity_data:
    for name in entity_data["names"]:
        if "kind" not in name:
            print("Name missing 'kind' field")
        if "en" not in name and "ne" not in name:
            print("Name must have 'en' or 'ne' field")
```

---

## Additional Resources

- [Data Models](data-models.md) - Entity and relationship schemas
- [Search Service Guide](search-service-guide.md) - Querying entities
- [Migration Contributor Guide](migration-contributor-guide.md) - Using Publication Service in migrations
- [Data Maintainer Guide](data-maintainer-guide.md) - Complete maintenance workflows

---

**Last Updated:** 2024  
**Version:** 2.0
