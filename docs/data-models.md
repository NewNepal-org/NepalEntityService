# Data Models

This document describes the data models used in the Nepal Entity Service. All models are defined using Pydantic for validation and serialization.

## Entity Model

Entities represent persons, organizations, and locations in Nepal's political and administrative landscape.

### Entity Schema

```json
{
  "id": "string (computed)",
  "slug": "string (required, 3-50 chars, kebab-case)",
  "type": "person | organization | location",
  "sub_type": "string (optional, depends on type)",
  "names": [
    {
      "kind": "PRIMARY | ALIAS | ALTERNATE | BIRTH | OFFICIAL",
      "en": {
        "full": "string",
        "first": "string (optional)",
        "middle": "string (optional)",
        "last": "string (optional)",
        "prefix": "string (optional)",
        "suffix": "string (optional)"
      },
      "ne": {
        "full": "string",
        "first": "string (optional)",
        "middle": "string (optional)",
        "last": "string (optional)",
        "prefix": "string (optional)",
        "suffix": "string (optional)"
      }
    }
  ],
  "version_summary": {
    "version": "integer",
    "created_at": "datetime",
    "created_by": "string"
  },
  "identifiers": [
    {
      "scheme": "string (e.g., wikipedia, wikidata, twitter)",
      "value": "string",
      "url": "string (optional)"
    }
  ],
  "attributes": {
    "key": "value (flexible key-value pairs)"
  },
  "contacts": [
    {
      "type": "EMAIL | PHONE | URL | ADDRESS",
      "value": "string"
    }
  ],
  "descriptions": {
    "en": {
      "value": "string",
      "provenance": "human | llm | scraped"
    },
    "ne": {
      "value": "string",
      "provenance": "human | llm | scraped"
    }
  }
}
```

### Entity Types and Subtypes

#### Person

Represents individual persons (politicians, public officials, etc.).

**Type**: `person`

**Subtypes**: None (persons don't have subtypes)

**Common Attributes**:
- `party`: Political party affiliation
- `position`: Current position or role
- `occupation`: Primary occupation
- `birth_date`: Date of birth
- `birth_place`: Place of birth

**Example**:

```json
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
  "attributes": {
    "party": "nepali-congress",
    "position": "president",
    "birth_date": "1944-10-06"
  }
}
```

#### Organization

Represents organizations, institutions, and groups.

**Type**: `organization`

**Subtypes**:
- `political_party`: Political parties
- `government_body`: Government ministries, departments, agencies
- `ngo`: Non-governmental organizations
- `private_company`: Private sector companies
- `international_org`: International organizations

**Common Attributes**:
- `founded_date`: Date of establishment
- `headquarters`: Location of headquarters
- `website`: Official website URL
- `registration_number`: Official registration number

**Example**:

```json
{
  "id": "entity:organization/political_party/nepali-congress",
  "slug": "nepali-congress",
  "type": "organization",
  "sub_type": "political_party",
  "names": [
    {
      "kind": "PRIMARY",
      "en": {
        "full": "Nepali Congress"
      },
      "ne": {
        "full": "नेपाली कांग्रेस"
      }
    }
  ],
  "attributes": {
    "founded_date": "1947-01-25",
    "ideology": "social-democracy",
    "symbol": "tree"
  }
}
```

#### Location

Represents geographic locations in Nepal's administrative hierarchy.

**Type**: `location`

**Subtypes**:
- `province`: Federal provinces (7 provinces)
- `district`: Districts (77 districts)
- `metropolitan_city`: Metropolitan cities
- `sub_metropolitan_city`: Sub-metropolitan cities
- `municipality`: Municipalities
- `rural_municipality`: Rural municipalities
- `ward`: Electoral wards

**Common Attributes**:
- `code`: Official administrative code
- `population`: Population count
- `area_sq_km`: Area in square kilometers
- `parent_location`: Parent location ID

**Example**:

```json
{
  "id": "entity:location/province/bagmati",
  "slug": "bagmati",
  "type": "location",
  "sub_type": "province",
  "names": [
    {
      "kind": "PRIMARY",
      "en": {
        "full": "Bagmati Province"
      },
      "ne": {
        "full": "बागमती प्रदेश"
      }
    }
  ],
  "attributes": {
    "code": "3",
    "capital": "Hetauda",
    "population": "6101530",
    "area_sq_km": "20300"
  }
}
```

### Name Structure

Names support multilingual variants with structured components:

**Name Kinds**:
- `PRIMARY`: Main name used for the entity
- `ALIAS`: Alternative name or nickname
- `ALTERNATE`: Alternate spelling or transliteration
- `BIRTH`: Birth name (if different from current name)
- `OFFICIAL`: Official legal name

**Name Components**:
- `full`: Complete name (required)
- `first`: First name or given name
- `middle`: Middle name(s)
- `last`: Last name or family name
- `prefix`: Title or prefix (e.g., "Dr.", "Hon.")
- `suffix`: Suffix (e.g., "Jr.", "PhD")

### Identifiers

External identifiers link entities to other systems:

**Common Schemes**:
- `wikipedia`: Wikipedia page name
- `wikidata`: Wikidata Q-number
- `twitter`: Twitter handle
- `facebook`: Facebook page ID
- `official_website`: Official website URL
- `election_commission`: Election Commission ID

### Attributes

Flexible key-value pairs for entity-specific data. Common patterns:

**Person Attributes**:
- `party`, `position`, `occupation`
- `birth_date`, `birth_place`
- `education`, `alma_mater`

**Organization Attributes**:
- `founded_date`, `headquarters`
- `registration_number`, `website`
- `ideology`, `symbol`

**Location Attributes**:
- `code`, `population`, `area_sq_km`
- `parent_location`, `capital`

## Relationship Model

Relationships represent connections between entities.

### Relationship Schema

```json
{
  "id": "string (computed)",
  "source_entity_id": "string (required)",
  "target_entity_id": "string (required)",
  "type": "string (required)",
  "start_date": "date (optional)",
  "end_date": "date (optional)",
  "attributes": {
    "key": "value"
  },
  "version_summary": {
    "version": "integer",
    "created_at": "datetime",
    "created_by": "string"
  },
  "attributions": ["string"]
}
```

### Relationship Types

**Common Relationship Types**:

- `MEMBER_OF`: Person is a member of an organization
- `AFFILIATED_WITH`: Entity is affiliated with another entity
- `EMPLOYED_BY`: Person is employed by an organization
- `REPRESENTS`: Person represents a location (constituency)
- `LOCATED_IN`: Entity is located in a location
- `PART_OF`: Location is part of another location
- `LEADS`: Person leads an organization
- `FOUNDED`: Person founded an organization

### Temporal Relationships

Relationships can have start and end dates:

```json
{
  "source_entity_id": "entity:person/ram-chandra-poudel",
  "target_entity_id": "entity:organization/political_party/nepali-congress",
  "type": "MEMBER_OF",
  "start_date": "2000-01-01",
  "end_date": null,
  "attributes": {
    "role": "president",
    "status": "active"
  }
}
```

**Temporal Queries**:
- `currently_active=true`: Relationships without end date
- Date range filtering: Find relationships active during a period

### Relationship Attributes

Relationship-specific metadata:

**MEMBER_OF Attributes**:
- `role`: Role within organization
- `status`: active, inactive, suspended
- `membership_type`: full, associate, honorary

**REPRESENTS Attributes**:
- `constituency`: Electoral constituency
- `term_start`: Start of term
- `term_end`: End of term
- `election_year`: Year of election

**EMPLOYED_BY Attributes**:
- `position`: Job title
- `department`: Department or division
- `employment_type`: full-time, part-time, contract

## Version Model

Versions provide complete audit trails for entities and relationships.

### Version Schema

```json
{
  "entity_or_relationship_id": "string (required)",
  "version_number": "integer (required)",
  "actor": "string (required)",
  "created_at": "datetime (required)",
  "change_description": "string (optional)",
  "snapshot": {
    "...": "complete entity or relationship state"
  },
  "attribution": {
    "source": "string",
    "confidence": "number",
    "method": "string"
  }
}
```

### Version History

Every change creates a new version:

1. **Version 1**: Initial creation
2. **Version 2**: First update
3. **Version 3**: Second update
4. ...and so on

**Version Metadata**:
- `version_number`: Sequential version number
- `actor`: Who made the change (actor ID)
- `created_at`: When the change was made
- `change_description`: Why the change was made
- `snapshot`: Complete state at that version

### Actor Model

Actors represent who made changes:

**Actor Types**:
- `actor:system:*`: System-generated changes (importers, scrapers)
- `actor:human:*`: Human data maintainers
- `actor:api:*`: API-initiated changes (future)

**Example Actors**:
- `actor:system:csv-importer`: CSV import script
- `actor:system:wikipedia-scraper`: Wikipedia scraper
- `actor:human:data-maintainer`: Human data maintainer
- `actor:human:researcher`: Research team member

## Validation Rules

### Entity Validation

- **Slug**: 3-50 characters, kebab-case, lowercase
- **Names**: At least one name with `kind="PRIMARY"`
- **Type**: Must be `person`, `organization`, or `location`
- **Subtype**: Must be valid for the entity type

### Relationship Validation

- **Entity IDs**: Both source and target must exist
- **Type**: Must be a valid relationship type
- **Dates**: `end_date` must be after `start_date`
- **Circular References**: Prevented for hierarchical relationships

### Name Validation

- **Full Name**: Required for all names
- **Language**: At least one language (en or ne) required
- **Components**: If provided, must be consistent with full name

## Data Quality

### Provenance Tracking

All data includes provenance information:

- **Source**: Where the data came from
- **Method**: How it was obtained (human, llm, scraped)
- **Confidence**: Confidence level (0.0-1.0)
- **Timestamp**: When it was added

### Change Descriptions

All changes should include descriptions:

```json
{
  "change_description": "Updated party affiliation based on official announcement"
}
```

## Examples

### Complete Person Entity

```json
{
  "id": "entity:person/sher-bahadur-deuba",
  "slug": "sher-bahadur-deuba",
  "type": "person",
  "names": [
    {
      "kind": "PRIMARY",
      "en": {
        "full": "Sher Bahadur Deuba",
        "first": "Sher Bahadur",
        "last": "Deuba"
      },
      "ne": {
        "full": "शेर बहादुर देउबा"
      }
    }
  ],
  "version_summary": {
    "version": 3,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "actor:human:data-maintainer"
  },
  "identifiers": [
    {
      "scheme": "wikipedia",
      "value": "Sher_Bahadur_Deuba",
      "url": "https://en.wikipedia.org/wiki/Sher_Bahadur_Deuba"
    },
    {
      "scheme": "wikidata",
      "value": "Q57363"
    }
  ],
  "attributes": {
    "party": "nepali-congress",
    "position": "prime-minister",
    "birth_date": "1946-06-13",
    "birth_place": "Dadeldhura"
  },
  "contacts": [],
  "descriptions": {
    "en": {
      "value": "Nepali politician who has served as Prime Minister of Nepal five times",
      "provenance": "human"
    },
    "ne": {
      "value": "नेपाली राजनीतिज्ञ जसले पाँच पटक नेपालको प्रधानमन्त्रीको रूपमा सेवा गरेका छन्",
      "provenance": "human"
    }
  }
}
```

### Complete Relationship

```json
{
  "id": "relationship:abc123def456",
  "source_entity_id": "entity:person/sher-bahadur-deuba",
  "target_entity_id": "entity:organization/political_party/nepali-congress",
  "type": "MEMBER_OF",
  "start_date": "1990-01-01",
  "end_date": null,
  "attributes": {
    "role": "president",
    "status": "active",
    "membership_type": "full"
  },
  "version_summary": {
    "version": 2,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "actor:human:data-maintainer"
  },
  "attributions": [
    "https://nepalikhabar.com/article/...",
    "Official party records"
  ]
}
```

## Next Steps

- [API Reference](/api-reference) - Learn how to query these models
- [Examples](/examples) - See real-world usage examples
- [Getting Started](/getting-started) - Start using the API
