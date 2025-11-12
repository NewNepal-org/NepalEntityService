# Migrations Directory

This directory contains versioned migration folders for managing database evolution in the Nepal Entity Service.

## Overview

Migrations are a way to systematically update the database content through versioned, reviewable, and reproducible scripts. Each migration is a folder containing:
- A Python script (`migrate.py`) that performs the data changes
- A README documenting the purpose and approach
- Optional data files (CSV, Excel, JSON) used by the migration

## Migration Structure

Each migration folder follows this naming convention:
```
NNN-descriptive-name/
├── migrate.py          # Main migration script (required)
├── README.md           # Documentation (required)
└── data.csv            # Optional data files
```

Where:
- `NNN` is a 3-digit numeric prefix (000-999) determining execution order
- `descriptive-name` is a kebab-case description of what the migration does

## Migration Script Template

```python
"""
Migration: NNN-descriptive-name
Description: Brief description of what this migration does
Author: your-email@example.com
Date: YYYY-MM-DD
"""

# Migration metadata
AUTHOR = "your-email@example.com"
DATE = "YYYY-MM-DD"
DESCRIPTION = "Brief description of what this migration does"

async def migrate(context):
    """
    Main migration function.
    
    Args:
        context: MigrationContext with access to services and data
    """
    # Your migration logic here
    context.log("Migration started")
    
    # Example: Read data from CSV
    # data = context.read_csv("data.csv")
    
    # Example: Create entities
    # for row in data:
    #     entity = Entity(...)
    #     await context.publication.create_entity(entity, author_id, description)
    
    context.log("Migration completed")
```

## Available Context Methods

The `context` object passed to your migration provides:

### Services
- `context.publication` - Publication Service for creating/updating entities
- `context.search` - Search Service for querying entities
- `context.scraping` - Scraping Service for data normalization
- `context.db` - Direct database access (read-only)

### File Helpers
- `context.read_csv(filename)` - Read CSV file from migration folder
- `context.read_json(filename)` - Read JSON file from migration folder
- `context.read_excel(filename, sheet_name)` - Read Excel file from migration folder

### Utilities
- `context.migration_dir` - Path to the migration folder
- `context.log(message)` - Log a message during migration execution

## Creating a Migration

1. **Copy the example migration**:
   ```bash
   cp -r migrations/000-example-migration migrations/001-your-migration-name
   ```

2. **Update the metadata** in `migrate.py`:
   - Set `AUTHOR` to your email
   - Set `DATE` to today's date (YYYY-MM-DD)
   - Set `DESCRIPTION` to describe what the migration does

3. **Implement the migration logic** in the `migrate()` function

4. **Document the migration** in `README.md`:
   - Purpose: What does this migration do?
   - Data Sources: Where does the data come from?
   - Changes: What entities/relationships are created/updated?
   - Dependencies: Does this depend on other migrations?
   - Notes: Any special considerations?

5. **Add data files** if needed (CSV, Excel, JSON)

6. **Test locally** (if you have the database setup):
   ```bash
   nes migration run 001-your-migration-name
   ```

7. **Submit a pull request** with your migration folder

## Migration Workflow

1. **Contributor** creates migration folder and submits PR
2. **CI/CD** validates migration structure and executes it in test environment
3. **Maintainer** reviews migration code and generated statistics
4. **Automated service** executes approved migrations and persists to Database Repository
5. **Git history** tracks all applied migrations with full metadata

## Checking Migration Status

Use the Migration Manager to check migration status:

```python
from pathlib import Path
from nes.services.migration import MigrationManager

manager = MigrationManager(Path("migrations"), Path("nes-db"))

# Discover all migrations
migrations = await manager.discover_migrations()

# Check which migrations have been applied
applied = await manager.get_applied_migrations()

# Check which migrations are pending
pending = await manager.get_pending_migrations()

# Check if a specific migration is applied
is_applied = await manager.is_migration_applied(migration)
```

Or run the demo script:
```bash
python examples/migration_manager_demo.py
```

## Best Practices

1. **Keep migrations focused**: Each migration should do one thing well
2. **Document thoroughly**: Future maintainers will thank you
3. **Include data sources**: Document where the data comes from
4. **Test before submitting**: Validate your migration locally if possible
5. **Use descriptive names**: Make it clear what the migration does
6. **Follow the template**: Use the example migration as a starting point

## Example Migrations

- `000-example-migration/` - Template and example migration structure

## Questions?

See the main documentation or ask in the project's discussion forum.
