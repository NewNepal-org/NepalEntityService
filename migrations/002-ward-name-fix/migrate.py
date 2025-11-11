"""
Migration: 002-ward-name-fix
Description: [TODO: Describe what this migration does]
Author: Damodar Dahal
Date: 2025-11-11
"""

from nes.services.migration.context import MigrationContext

# Migration metadata (used for Git commit message)
AUTHOR = "Damodar Dahal"
DATE = "2025-11-11"
DESCRIPTION = "[TODO: Describe what this migration does]"


async def migrate(context: MigrationContext) -> None:
    """
    Main migration function.

    This function is called by the migration runner to execute the migration.
    It receives a MigrationContext object that provides access to services
    and helper functions.

    Args:
        context: MigrationContext with access to services and utilities

    Available Services:
    -------------------

    context.publication - PublicationService
        Create and update entities and relationships with full versioning.

        Methods:
            await context.publication.create_entity(entity, author_id, change_description)
            await context.publication.update_entity(entity_id, updates, author_id, change_description)
            await context.publication.create_relationship(relationship, author_id, change_description)

    context.search - SearchService
        Search and query existing entities.

        Methods:
            await context.search.search_entities(query, **filters)
            await context.search.find_entity_by_name(name, entity_type=None)
            await context.search.get_entity(entity_id)

    context.scraping - ScrapingService
        Extract and normalize data from various sources.

        Methods:
            await context.scraping.normalize_name(raw_name, language="ne")
            await context.scraping.extract_data(source, **options)

    context.db - EntityDatabase
        Direct read access to the entity database.

        Methods:
            context.db.get_entity(entity_id)
            context.db.list_entities(entity_type=None)
            context.db.get_relationships(entity_id)

    File Reading Helpers:
    ---------------------

    context.read_csv(filename)
        Read CSV file from migration folder as list of dictionaries.

        Example:
            data = context.read_csv("entities.csv")
            for row in data:
                print(row["name"], row["type"])

    context.read_json(filename)
        Read JSON file from migration folder.

        Example:
            config = context.read_json("config.json")
            print(config["setting"])

    context.read_excel(filename, sheet_name=None)
        Read Excel file from migration folder as list of dictionaries.
        Requires openpyxl to be installed.

        Example:
            data = context.read_excel("data.xlsx", sheet_name="Sheet1")
            for row in data:
                print(row["name"], row["value"])

    Logging:
    --------

    context.log(message)
        Log a message during migration execution.
        Messages are displayed in console and included in migration results.

        Example:
            context.log("Processing 100 entities...")
            context.log(f"Imported {count} entities successfully")

    Migration Directory:
    --------------------

    context.migration_dir
        Path to the migration folder containing this script.
        Use this to construct paths to data files.

        Example:
            data_file = context.migration_dir / "data.csv"

    Common Patterns:
    ----------------

    1. Import entities from CSV:

        data = context.read_csv("entities.csv")
        author_id = "author:migration:002-ward-name-fix"

        for row in data:
            entity = Entity(
                slug=row["slug"],
                type=EntityType.PERSON,
                names=[Name(
                    kind=NameKind.PRIMARY,
                    en=NameParts(full=row["name_en"]),
                    ne=NameParts(full=row["name_ne"])
                )]
            )

            await context.publication.create_entity(
                entity=entity,
                author_id=author_id,
                change_description=f"Import {{row['name_en']}}"
            )

        context.log(f"Imported {{len(data)}} entities")

    2. Update existing entities:

        entities = context.db.list_entities(entity_type=EntityType.PERSON)
        author_id = "author:migration:002-ward-name-fix"

        for entity in entities:
            updates = {{
                "attributes": {{
                    "verified": True
                }}
            }}

            await context.publication.update_entity(
                entity_id=entity.id,
                updates=updates,
                author_id=author_id,
                change_description="Mark as verified"
            )

        context.log(f"Updated {{len(entities)}} entities")

    3. Create relationships:

        data = context.read_csv("relationships.csv")
        author_id = "author:migration:002-ward-name-fix"

        for row in data:
            relationship = Relationship(
                from_entity_id=row["from_id"],
                to_entity_id=row["to_id"],
                type=RelationshipType.MEMBER_OF,
                attributes={{"role": row["role"]}}
            )

            await context.publication.create_relationship(
                relationship=relationship,
                author_id=author_id,
                change_description=f"Link {{row['from_id']}} to {{row['to_id']}}"
            )

        context.log(f"Created {{len(data)}} relationships")

    4. Search and update:

        author_id = "author:migration:002-ward-name-fix"

        # Find entity by name
        entity = await context.search.find_entity_by_name(
            "Ram Chandra Poudel",
            entity_type=EntityType.PERSON
        )

        if entity:
            updates = {{"attributes": {{"title": "President"}}}}
            await context.publication.update_entity(
                entity_id=entity.id,
                updates=updates,
                author_id=author_id,
                change_description="Update title"
            )
            context.log(f"Updated {{entity.id}}")
        else:
            context.log("Entity not found")

    5. Normalize names:

        data = context.read_csv("entities.csv")

        for row in data:
            # Normalize Nepali name
            normalized = await context.scraping.normalize_name(
                row["name_ne"],
                language="ne"
            )

            context.log(f"Normalized: {{row['name_ne']}} -> {{normalized}}")
    """
    author_id = "author:damodar-dahal"

    wards = await context.search.search_entities(
        entity_type="location", sub_type="ward", limit=10_000
    )

    for ward in wards:
        if "-" in ward.names[0].en.full:
            parent = await context.db.get_entity(ward.parent)

            parent_name = parent.names[0].en.full
            ward_no = ward.names[0].en.full.split(" ")[-1]
            ward_name = f"{parent_name} - Ward {ward_no}"

            ward.names[0].en.full = ward_name

            await context.publication.update_entity(
                entity=ward, author_id=author_id, change_description="Fix ward name"
            )

    context.log("Migration completed")
