# Nepal Entity Service - Usage Examples

This document provides an overview of all available examples, notebooks, and documentation for the Nepal Entity Service (nes).

## Quick Start

1. **Install the package:**
   ```bash
   poetry install
   ```

2. **Choose your learning path:**
   - **Quick examples:** Start with Python scripts in `examples/`
   - **Interactive learning:** Use Jupyter notebooks in `notebooks/`
   - **Reference guide:** Read the Data Maintainer Guide in `docs/`

## Example Scripts (`examples/`)

Ready-to-run Python scripts demonstrating common operations with authentic Nepali data.

### Available Scripts

| Script | Description | Use Case |
|--------|-------------|----------|
| `update_entity.py` | Update an entity with automatic versioning | Modify existing entity data |
| `create_relationship.py` | Create relationships between entities | Link politicians to parties |
| `batch_import.py` | Import multiple entities at once | Bulk data operations |
| `version_history.py` | Explore version history and audit trails | Track changes over time |

### Running Examples

```bash
# Run any example script
python examples/update_entity.py
python examples/create_relationship.py
python examples/batch_import.py
python examples/version_history.py
```

**See:** `examples/README.md` for detailed information

## Jupyter Notebooks (`notebooks/`)

Interactive tutorials for hands-on learning with step-by-step explanations.

### Available Notebooks

| Notebook | Topics | Best For |
|----------|--------|----------|
| `01_entity_management.ipynb` | Create, update, search entities | Getting started |
| `02_relationship_management.ipynb` | Manage entity relationships | Understanding connections |
| `03_data_import_workflow.ipynb` | Complete import workflow | Bulk data operations |
| `04_data_quality_analysis.ipynb` | Analyze and improve data quality | Maintaining quality |

### Running Notebooks

```bash
# Install Jupyter
poetry add --group dev jupyter

# Start Jupyter
poetry run jupyter notebook

# Or use JupyterLab
poetry add --group dev jupyterlab
poetry run jupyter lab
```

**See:** `notebooks/README.md` for detailed information

## Documentation (`docs/`)

Comprehensive guides and reference documentation.

### Data Maintainer Guide

**Location:** `docs/data-maintainer-guide.md`

**Contents:**
- Publication Service API reference
- Common operations with code examples
- Working with Nepali multilingual data
- Best practices for data maintenance
- Troubleshooting guide
- Complete workflow examples

**Best for:** Reference while building data maintenance tools

### Other Documentation

- `docs/getting-started.md` - Quick start guide
- `docs/architecture.md` - System architecture
- `docs/api-reference.md` - API endpoint documentation
- `docs/data-models.md` - Entity and relationship schemas
- `docs/examples.md` - Additional code examples

## Learning Paths

### Path 1: Quick Start (30 minutes)

1. Read `docs/getting-started.md`
2. Run `examples/update_entity.py`
3. Run `examples/create_relationship.py`
4. Explore the API at `/docs` (start server first)

### Path 2: Interactive Learning (2 hours)

1. Open `notebooks/01_entity_management.ipynb`
2. Work through `notebooks/02_relationship_management.ipynb`
3. Try `notebooks/03_data_import_workflow.ipynb`
4. Review `docs/data-maintainer-guide.md`

### Path 3: Deep Dive (4+ hours)

1. Read all documentation in `docs/`
2. Work through all notebooks in `notebooks/`
3. Study all example scripts in `examples/`
4. Build your own data maintenance tools
5. Explore the test files in `tests/` for advanced patterns

## Common Use Cases

### Use Case 1: Import New Politicians

**Tools:**
- Example: `examples/batch_import.py`
- Notebook: `notebooks/03_data_import_workflow.ipynb`
- Guide: `docs/data-maintainer-guide.md` → "Creating a Politician Entity"

### Use Case 2: Update Entity Information

**Tools:**
- Example: `examples/update_entity.py`
- Notebook: `notebooks/01_entity_management.ipynb`
- Guide: `docs/data-maintainer-guide.md` → "Update Entity"

### Use Case 3: Create Party Memberships

**Tools:**
- Example: `examples/create_relationship.py`
- Notebook: `notebooks/02_relationship_management.ipynb`
- Guide: `docs/data-maintainer-guide.md` → "Create Relationship"

### Use Case 4: Track Changes Over Time

**Tools:**
- Example: `examples/version_history.py`
- Notebook: `notebooks/01_entity_management.ipynb` → "View Version History"
- Guide: `docs/data-maintainer-guide.md` → "Get Entity Versions"

### Use Case 5: Analyze Data Quality

**Tools:**
- Notebook: `notebooks/04_data_quality_analysis.ipynb`
- Guide: `docs/data-maintainer-guide.md` → "Best Practices"

## Authentic Nepali Data

All examples use authentic Nepali political data including:

### Politicians
- Pushpa Kamal Dahal (Prachanda) - CPN Maoist Centre
- Sher Bahadur Deuba - Nepali Congress
- KP Sharma Oli - CPN-UML
- Ram Chandra Poudel - President of Nepal
- Gagan Thapa - Nepali Congress
- Rabi Lamichhane - Rastriya Swatantra Party

### Political Parties
- Nepali Congress (नेपाली कांग्रेस)
- CPN-UML (ने.क.पा. एमाले)
- CPN Maoist Centre (ने.क.पा. माओवादी केन्द्र)
- Rastriya Swatantra Party (राष्ट्रिय स्वतन्त्र पार्टी)
- Nepal Samajbadi Party (नेपाल समाजवादी पार्टी)

### Locations
- 7 Provinces (Koshi, Madhesh, Bagmati, Gandaki, Lumbini, Karnali, Sudurpashchim)
- Districts (Kathmandu, Lalitpur, Morang, Kaski, etc.)
- Municipalities (Kathmandu Metropolitan City, Pokhara, etc.)

All names include both English and Nepali (Devanagari) variants.

## API Documentation

Start the server to access interactive API documentation:

```bash
# Start development server
poetry run nes server dev

# Or production server
poetry run nes server start
```

Then visit:
- **Root Documentation:** http://localhost:8195/
- **API Schema:** http://localhost:8195/docs
- **Health Check:** http://localhost:8195/api/health

## Code Patterns

### Initialize Services

```python
from pathlib import Path
from nes.database.file_database import FileDatabase
from nes.services.publication import PublicationService

db = FileDatabase(base_path="nes-db/v2")
pub_service = PublicationService(database=db)
```

### Create Entity

```python
entity = await pub_service.create_entity(
    entity_data={
        "slug": "entity-slug",
        "type": "person",
        "names": [{"kind": "PRIMARY", "en": {"full": "Name"}, "ne": {"full": "नाम"}}]
    },
    author_id="author:human:data-maintainer",
    change_description="Description of change"
)
```

### Update Entity

```python
entity = await pub_service.get_entity(entity_id)
entity.attributes["key"] = "value"
updated = await pub_service.update_entity(
    entity=entity,
    author_id="author:human:data-maintainer",
    change_description="Updated attribute"
)
```

### Create Relationship

```python
relationship = await pub_service.create_relationship(
    source_entity_id="entity:person/politician-slug",
    target_entity_id="entity:organization/political_party/party-slug",
    relationship_type="MEMBER_OF",
    author_id="author:human:data-maintainer",
    change_description="Added membership"
)
```

## Testing Your Code

Run the test suite to see more examples:

```bash
# Run all tests
poetry run pytest tests/

# Run specific test file
poetry run pytest tests/services/test_publication_service.py

# Run with coverage
poetry run pytest tests/ --cov=nes
```

## Getting Help

1. **Documentation:** Check `docs/` directory
2. **Examples:** Review `examples/` and `notebooks/`
3. **Tests:** Look at `tests/` for advanced patterns
4. **API Docs:** Visit `/docs` when server is running

## Contributing

When creating new examples or documentation:

1. Use authentic Nepali data
2. Include both English and Nepali names
3. Follow existing patterns and structure
4. Add clear explanations and comments
5. Test your code before committing

## Next Steps

1. Choose a learning path above
2. Work through the examples
3. Build your own data maintenance tools
4. Contribute improvements back to the project

---

**Version:** 2.0  
**Last Updated:** November 2024
