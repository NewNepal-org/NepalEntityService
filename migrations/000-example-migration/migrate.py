"""
Migration: 000-example-migration
Description: Create initial example entity - BP Koirala
Author: system@nepalentity.org
Date: 2024-11-08
"""

from nes.services.migration.context import MigrationContext

# Migration metadata (used for Git commit message)
AUTHOR = "system@nepalentity.org"
DATE = "2024-11-08"
DESCRIPTION = "Create initial example entity - BP Koirala"


async def migrate(context: MigrationContext):
    """
    Create the first entity in the database - BP Koirala.

    This migration creates a person entity for Bishweshwar Prasad Koirala,
    the first democratically elected Prime Minister of Nepal.

    Args:
        context: MigrationContext with access to services and data
    """
    context.log("Starting migration: Creating BP Koirala entity")

    # Create author for this migration
    author_id = "migration-000-example-migration"

    # Create BP Koirala entity data
    entity_data = {
        "slug": "bishweshwar-prasad-koirala",
        "type": "person",
        "names": [
            {
                "kind": "PRIMARY",
                "en": {
                    "full": "Bishweshwar Prasad Koirala",
                    "given": "Bishweshwar Prasad",
                    "family": "Koirala",
                },
                "ne": {"full": "विश्वेश्वर प्रसाद कोइराला"},
            },
            {
                "kind": "ALIAS",
                "en": {"full": "BP Koirala"},
                "ne": {"full": "बी पी कोइराला"},
            },
        ],
    }

    # Create the entity using the publication service
    created_entity = await context.publication.create_entity(
        entity_data=entity_data,
        author_id=author_id,
        change_description="Initial migration: Create BP Koirala entity",
    )

    context.log(f"Created entity: {created_entity.slug}")
    context.log("Migration completed successfully")
