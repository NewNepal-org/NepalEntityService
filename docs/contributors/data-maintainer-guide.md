# Data Maintainer Guide

This guide is for data maintainers who manage entity data in the Nepal Entity Service (nes). It covers the Publication Service API, common operations, best practices, and troubleshooting.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Publication Service API](#publication-service-api)
4. [Common Operations](#common-operations)
5. [Working with Nepali Data](#working-with-nepali-data)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

---

## Introduction

The Nepal Entity Service provides a Pythonic interface for data maintenance through the **Publication Service**. This service handles:

- Entity lifecycle management (create, update, delete)
- Automatic versioning for all changes
- Relationship management with bidirectional consistency
- Author attribution tracking
- Business rule enforcement

### Who This Guide Is For

- Data maintainers managing entity databases
- Developers building data import tools
- Researchers curating political data
- Anyone maintaining Nepali public entity information

### What You'll Learn

- How to use the Publication Service API
- Best practices for data maintenance
- How to work with multilingual Nepali data
- Common patterns and workflows
- Troubleshooting techniques

---

## Getting Started

### Installation

Install the nes package using poetry:

```bash
poetry install
```

### Initialize Services

```python
from pathlib import Path
from nes.database.file_database import FileDatabase
from nes.services.publication import PublicationService

# Initialize database
db_path = Path("nes-db/v2")
db = FileDatabase(base_path=str(db_path))

# Initialize publication service
pub_service = PublicationService(database=db)
```

### Database Location

By default, all entity data is stored in `nes-db/v2/`. The directory structure is:

```
nes-db/v2/
├── entity/
│   ├── person/
│   │   └── {slug}.json
│   ├── organization/
│   │   ├── political_party/
│   │   │   └── {slug}.json
│   │   └── government_body/
│   │       └── {slug}.json
│   └── location/
│       ├── province/
│       │   └── {slug}.json
│       └── district/
│           └── {slug}.json
├── relationship/
│   └── {relationship-id}.json
├── version/
│   ├── entity/
│   │   └── {entity-id}/
│   │       └── {version-number}.json
│   └── relationship/
│       └── {relationship-id}/
│           └── {version-number}.json
└── author/
    └── {slug}.json
```

---

## Publication Service API

The Publication Service is the central interface for all data maintenance operations.

### Entity Operations

#### Create Entity

```python
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
        ],
        "attributes": {
            "party": "nepali-congress",
            "position": "President"
        }
    },
    author_id="author:human:data-maintainer",
    change_description="Initial import from official records"
)
```

**Parameters:**
- `entity_data` (dict): Entity data following the entity schema
- `author_id` (str): ID of the author creating the entity
- `change_description` (str): Description of this change

**Returns:** Created entity with version 1

**Raises:**
- `ValueError`: If entity data is invalid or entity already exists

#### Get Entity

```python
entity = await pub_service.get_entity("entity:person/ram-chandra-poudel")
```

**Parameters:**
- `entity_id` (str): The unique identifier of the entity

**Returns:** Entity if found, None otherwise

#### Update Entity

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
```

**Parameters:**
- `entity` (Entity): Entity to update (with modifications)
- `author_id` (str): ID of the author updating the entity
- `change_description` (str): Description of this change

**Returns:** Updated entity with incremented version number

**Raises:**
- `ValueError`: If entity doesn't exist or update is invalid

#### Delete Entity

```python
success = await pub_service.delete_entity("entity:person/ram-chandra-poudel")
```

**Parameters:**
- `entity_id` (str): The unique identifier of the entity to delete

**Returns:** True if deleted, False if entity didn't exist

**Note:** This is a hard delete. Version history is preserved but the entity is removed.

#### Get Entity Versions

```python
versions = await pub_service.get_entity_versions("entity:person/ram-chandra-poudel")

for version in versions:
    print(f"Version {version.version_number}")
    print(f"  Created: {version.created_at}")
    print(f"  Author: {version.author.slug}")
    print(f"  Description: {version.change_description}")
```

**Parameters:**
- `entity_id` (str): The unique identifier of the entity

**Returns:** List of Version objects, ordered by version number

### Relationship Operations

#### Create Relationship

```python
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
```

**Parameters:**
- `source_entity_id` (str): Source entity ID
- `target_entity_id` (str): Target entity ID
- `relationship_type` (str): Type of relationship (MEMBER_OF, HOLDS_POSITION, etc.)
- `start_date` (date, optional): When the relationship started
- `end_date` (date, optional): When the relationship ended
- `attributes` (dict, optional): Additional relationship metadata
- `author_id` (str): ID of the author creating the relationship
- `change_description` (str): Description of this change

**Returns:** Created relationship with version 1

**Raises:**
- `ValueError`: If entities don't exist or relationship is invalid

#### Update Relationship

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
```

**Parameters:**
- `relationship` (Relationship): Relationship to update (with modifications)
- `author_id` (str): ID of the author updating the relationship
- `change_description` (str): Description of this change

**Returns:** Updated relationship with incremented version number

#### Get Relationship Versions

```python
versions = await pub_service.get_relationship_versions(relationship_id)
```

**Parameters:**
- `relationship_id` (str): The unique identifier of the relationship

**Returns:** List of Version objects for the relationship

---

## Common Operations

### Creating a Politician Entity

```python
politician_data = {
    "slug": "pushpa-kamal-dahal",
    "type": "person",
    "sub_type": "politician",
    "names": [
        {
            "kind": "PRIMARY",
            "en": {
                "full": "Pushpa Kamal Dahal",
                "given": "Pushpa Kamal",
                "family": "Dahal"
            },
            "ne": {
                "full": "पुष्पकमल दाहाल",
                "given": "पुष्पकमल",
                "family": "दाहाल"
            }
        },
        {
            "kind": "ALIAS",
            "en": {"full": "Prachanda"},
            "ne": {"full": "प्रचण्ड"}
        }
    ],
    "attributes": {
        "party": "nepal-communist-party-maoist-centre",
        "constituency": "Gorkha-2",
        "positions": ["Prime Minister", "Party Chairman"]
    }
}

entity = await pub_service.create_entity(
    entity_data=politician_data,
    author_id="author:human:data-maintainer",
    change_description="Initial import"
)
```

### Creating a Political Party Entity

```python
party_data = {
    "slug": "nepali-congress",
    "type": "organization",
    "sub_type": "political_party",
    "names": [
        {
            "kind": "PRIMARY",
            "en": {"full": "Nepali Congress"},
            "ne": {"full": "नेपाली कांग्रेस"}
        },
        {
            "kind": "ALIAS",
            "en": {"full": "NC"},
            "ne": {"full": "ने.कां."}
        }
    ],
    "attributes": {
        "founded": "1947",
        "ideology": ["Social Democracy", "Democratic Socialism"],
        "headquarters": "Sanepa, Lalitpur",
        "symbol": "Tree"
    }
}

entity = await pub_service.create_entity(
    entity_data=party_data,
    author_id="author:human:data-maintainer",
    change_description="Initial import"
)
```

### Creating a Location Entity

```python
province_data = {
    "slug": "bagmati-province",
    "type": "location",
    "sub_type": "province",
    "names": [
        {
            "kind": "PRIMARY",
            "en": {"full": "Bagmati Province"},
            "ne": {"full": "बागमती प्रदेश"}
        }
    ],
    "attributes": {
        "number": 3,
        "capital": "Hetauda",
        "area_km2": 20300,
        "districts": 13
    }
}

entity = await pub_service.create_entity(
    entity_data=province_data,
    author_id="author:human:data-maintainer",
    change_description="Initial import"
)
```

### Batch Import

```python
async def batch_import_entities(entities_data, author_id):
    """Import multiple entities with error handling."""
    stats = {"created": 0, "updated": 0, "failed": 0, "errors": []}
    
    for entity_data in entities_data:
        try:
            from nes.core.identifiers import build_entity_id
            entity_id = build_entity_id(
                entity_data["type"],
                entity_data.get("sub_type"),
                entity_data["slug"]
            )
            
            existing = await pub_service.get_entity(entity_id)
            
            if existing:
                # Update existing
                if not existing.attributes:
                    existing.attributes = {}
                existing.attributes.update(entity_data.get("attributes", {}))
                
                await pub_service.update_entity(
                    entity=existing,
                    author_id=author_id,
                    change_description="Batch update"
                )
                stats["updated"] += 1
            else:
                # Create new
                await pub_service.create_entity(
                    entity_data=entity_data,
                    author_id=author_id,
                    change_description="Batch import"
                )
                stats["created"] += 1
                
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append({
                "slug": entity_data.get("slug", "unknown"),
                "error": str(e)
            })
    
    return stats
```

---

## Working with Nepali Data

### Multilingual Names

Always provide both English and Nepali names:

```python
"names": [
    {
        "kind": "PRIMARY",
        "en": {
            "full": "Sher Bahadur Deuba",
            "given": "Sher Bahadur",
            "family": "Deuba"
        },
        "ne": {
            "full": "शेरबहादुर देउवा",
            "given": "शेरबहादुर",
            "family": "देउवा"
        }
    }
]
```

### Name Kinds

Use appropriate name kinds:

- **PRIMARY**: Official full name
- **ALIAS**: Common alternative name or nickname
- **ALTERNATE**: Alternative spelling or transliteration
- **BIRTH**: Birth name (if different from current name)
- **OFFICIAL**: Official government name

Example with alias:

```python
"names": [
    {
        "kind": "PRIMARY",
        "en": {"full": "Pushpa Kamal Dahal"},
        "ne": {"full": "पुष्पकमल दाहाल"}
    },
    {
        "kind": "ALIAS",
        "en": {"full": "Prachanda"},
        "ne": {"full": "प्रचण्ड"}
    }
]
```

### Nepali Administrative Structure

Use correct administrative divisions:

**Provinces (7):**
- Koshi Province (कोशी प्रदेश)
- Madhesh Province (मधेश प्रदेश)
- Bagmati Province (बागमती प्रदेश)
- Gandaki Province (गण्डकी प्रदेश)
- Lumbini Province (लुम्बिनी प्रदेश)
- Karnali Province (कर्णाली प्रदेश)
- Sudurpashchim Province (सुदूरपश्चिम प्रदेश)

**Location Subtypes:**
- `province`: Provincial level
- `district`: District level
- `metropolitan_city`: Metropolitan cities (6)
- `sub_metropolitan_city`: Sub-metropolitan cities
- `municipality`: Municipalities
- `rural_municipality`: Rural municipalities

### Political Party Data

Include authentic party information:

```python
"attributes": {
    "founded": "1947",
    "ideology": ["Social Democracy", "Democratic Socialism"],
    "headquarters": "Sanepa, Lalitpur",
    "symbol": "Tree",
    "abbreviation": {"en": "NC", "ne": "ने.कां."}
}
```

---

## Best Practices

### 1. Always Provide Change Descriptions

```python
# Good
await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Updated position after 2023 election results"
)

# Bad
await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Update"  # Too vague
)
```

### 2. Use Meaningful Author IDs

```python
# Good author IDs
"author:human:john-doe"
"author:system:wikipedia-importer"
"author:system:election-commission-sync"

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

### 5. Use Transactions for Related Operations

When creating entities and relationships together, handle failures:

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
        # If relationship creation fails, consider deleting the politician
        # or logging for manual cleanup
        print(f"Failed to create politician with party: {e}")
        raise
```

### 6. Document Data Sources

Use attributes to track data sources:

```python
"attributes": {
    "party": "nepali-congress",
    "data_source": "Election Commission of Nepal",
    "source_url": "https://election.gov.np/...",
    "verified_date": "2024-01-15"
}
```

### 7. Regular Version History Review

Periodically review version history to ensure quality:

```python
async def audit_recent_changes(days=7):
    """Audit changes in the last N days."""
    from datetime import datetime, timedelta, UTC
    
    cutoff = datetime.now(UTC) - timedelta(days=days)
    
    # Sample entities
    entities = await db.list_entities(limit=100)
    
    for entity in entities:
        versions = await pub_service.get_entity_versions(entity.id)
        recent = [v for v in versions if v.created_at >= cutoff]
        
        if recent:
            print(f"{entity.names[0].en.full}: {len(recent)} changes")
            for v in recent:
                print(f"  - {v.author.slug}: {v.change_description}")
```

---

## Troubleshooting

### Entity Already Exists

**Error:** `ValueError: Entity with slug 'X' and type 'Y' already exists`

**Solution:** Check if the entity exists first:

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

### Missing PRIMARY Name

**Error:** `ValueError: Entity must have at least one name with kind='PRIMARY'`

**Solution:** Ensure at least one name has `kind="PRIMARY"`:

```python
"names": [
    {
        "kind": "PRIMARY",  # Required
        "en": {"full": "Name"},
        "ne": {"full": "नाम"}
    }
]
```

### Invalid Relationship

**Error:** `ValueError: Entity X does not exist`

**Solution:** Verify both entities exist before creating relationship:

```python
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

### Version Conflicts

**Issue:** Multiple maintainers updating the same entity

**Solution:** Always get the latest version before updating:

```python
# Get latest version
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

### Database Path Issues

**Error:** Database not found or permission denied

**Solution:** Verify database path and permissions:

```python
from pathlib import Path

db_path = Path("nes-db/v2")

# Check if path exists
if not db_path.exists():
    print(f"Database path does not exist: {db_path}")
    db_path.mkdir(parents=True, exist_ok=True)

# Check permissions
if not db_path.is_dir():
    print(f"Path is not a directory: {db_path}")
```

---

## Examples

### Complete Workflow: Import Politician

```python
async def import_politician_complete():
    """Complete workflow for importing a politician."""
    
    # 1. Initialize services
    db = FileDatabase(base_path="nes-db/v2")
    pub_service = PublicationService(database=db)
    
    # 2. Prepare entity data
    politician_data = {
        "slug": "gagan-thapa",
        "type": "person",
        "sub_type": "politician",
        "names": [
            {
                "kind": "PRIMARY",
                "en": {"full": "Gagan Kumar Thapa"},
                "ne": {"full": "गगन कुमार थापा"}
            }
        ],
        "attributes": {
            "party": "nepali-congress",
            "constituency": "Kathmandu-4"
        }
    }
    
    # 3. Validate data
    is_valid, errors = validate_entity_data(politician_data)
    if not is_valid:
        print(f"Validation failed: {errors}")
        return
    
    # 4. Check for duplicates
    from nes.core.identifiers import build_entity_id
    entity_id = build_entity_id("person", "politician", "gagan-thapa")
    existing = await pub_service.get_entity(entity_id)
    
    if existing:
        print(f"Entity already exists: {entity_id}")
        return
    
    # 5. Create entity
    try:
        entity = await pub_service.create_entity(
            entity_data=politician_data,
            author_id="author:human:data-maintainer",
            change_description="Initial import from official records"
        )
        print(f"✓ Created: {entity.id}")
        
        # 6. Create party membership
        relationship = await pub_service.create_relationship(
            source_entity_id=entity.id,
            target_entity_id="entity:organization/political_party/nepali-congress",
            relationship_type="MEMBER_OF",
            author_id="author:human:data-maintainer",
            change_description="Add party membership"
        )
        print(f"✓ Created relationship: {relationship.id}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

# Run the workflow
await import_politician_complete()
```

### Search and Update Workflow

```python
async def update_politicians_by_party(party_slug, new_attribute):
    """Update all politicians from a specific party."""
    from nes.services.search import SearchService
    
    search_service = SearchService(database=db)
    
    # Find all politicians with this party
    results = await search_service.search_entities(
        entity_type="person",
        sub_type="politician",
        limit=100
    )
    
    updated_count = 0
    
    for entity in results:
        if entity.attributes and entity.attributes.get("party") == party_slug:
            # Update attribute
            entity.attributes.update(new_attribute)
            
            await pub_service.update_entity(
                entity=entity,
                author_id="author:system:batch-updater",
                change_description=f"Batch update: {list(new_attribute.keys())}"
            )
            updated_count += 1
    
    print(f"Updated {updated_count} politicians")

# Example usage
await update_politicians_by_party(
    "nepali-congress",
    {"election_2022": "participated"}
)
```

---

## Additional Resources

- **Example Scripts:** See `examples/` directory for complete working examples
- **Jupyter Notebooks:** Interactive tutorials in `notebooks/` directory
- **API Documentation:** Run the server and visit `/docs` for API reference
- **Architecture Guide:** See `docs/architecture.md` for system design
- **Data Models:** See `docs/data-models.md` for schema reference

---

## Support

For questions or issues:

1. Check this guide and other documentation
2. Review example scripts and notebooks
3. Check the API documentation
4. Review test files for additional examples

---

**Last Updated:** 2024
**Version:** 2.0
