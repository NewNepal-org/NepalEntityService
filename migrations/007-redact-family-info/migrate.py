"""
Migration: 007-redact-family-info
Description: Redact family information from PersonDetails for privacy reasons
Author: Damodar Dahal
Date: 2025-12-14
"""

from nes.services.migration.context import MigrationContext

# Migration metadata (used for Git commit message)
AUTHOR = "Damodar Dahal"
DATE = "2025-12-14"
DESCRIPTION = "Redact family information from PersonDetails for privacy reasons"


async def migrate(context: MigrationContext) -> None:
    """
    Redact family information from all person entities.

    This migration removes spouse_name, mother_name, and father_name fields
    from PersonDetails for all person entities to protect privacy.

    Args:
        context: MigrationContext with access to services and utilities
    """
    context.log("Starting migration: Redact family information")

    # Author ID for this migration
    author_id = "author:damodar-dahal"

    # Get all person entities from the database (with high limit for 7000+ persons)
    persons = await context.search.search_entities(entity_type="person", limit=10_000)
    context.log(f"Found {len(persons)} person entities")

    # Track statistics
    updated_count = 0
    skipped_count = 0

    # Process each person entity
    for person in persons:
        # Check if person has personal_details
        if not person.personal_details:
            skipped_count += 1
            continue

        # Check if any family fields are set
        has_family_info = (
            person.personal_details.spouse_name is not None
            or person.personal_details.mother_name is not None
            or person.personal_details.father_name is not None
        )

        if not has_family_info:
            skipped_count += 1
            continue

        # Truncate family fields
        person.personal_details.spouse_name = None
        person.personal_details.mother_name = None
        person.personal_details.father_name = None

        # Update the entity using the publication service
        await context.publication.update_entity(
            entity=person,
            author_id=author_id,
            change_description="Redact family information for privacy",
        )

        updated_count += 1

    context.log(f"Updated {updated_count} person entities")
    context.log(f"Skipped {skipped_count} person entities (no family info)")
    context.log("Migration completed successfully")
