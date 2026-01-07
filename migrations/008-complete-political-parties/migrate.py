"""
Migration: 008-complete-political-parties
Description: Complete the political party database by importing remaining parties (204-230)
Author: Damodar Dahal
Date: 2026-01-07
"""

from datetime import date

from nepali_date_utils import converter

from nes.core.models import (
    Address,
    Attribution,
    ExternalIdentifier,
    LangText,
    LangTextValue,
    Name,
    NameParts,
    PartySymbol,
)
from nes.core.models.base import NameKind
from nes.core.models.entity import EntitySubType, EntityType
from nes.core.utils.devanagari import transliterate_to_roman
from nes.core.utils.slug_helper import text_to_slug
from nes.services.migration.context import MigrationContext
from nes.services.scraping.normalization import NameExtractor

# Migration metadata
AUTHOR = "Damodar Dahal"
DATE = "2026-01-07"
DESCRIPTION = (
    "Complete the political party database by importing remaining parties (204-230)"
)
CHANGE_DESCRIPTION = "Import additional political parties"

name_extractor = NameExtractor()


def convert_nepali_date(date_str: str) -> date:
    """Convert Nepali date to date object."""
    date_roman = transliterate_to_roman(date_str)
    y, m, d = date_roman.split("/")
    date_bs = f"{y.zfill(4)}/{m.zfill(2)}/{d.zfill(2)}"
    date_ad = converter.bs_to_ad(date_bs)
    y, m, d = date_ad.split("/")
    return date(int(y), int(m), int(d))


reg_no_external_identifier = LangText(
    en=LangTextValue(
        value="Election Commission Registration Number (2082)", provenance="human"
    ),
    ne=LangTextValue(value="निर्वाचन आयोग दर्ता नं.", provenance="human"),
)


async def update_national_independent_party_name(
    context: MigrationContext, author_id: str
) -> None:
    """
    Update National Independent Party to use Rastriya Swatantra Party as primary name.
    """
    context.log("Updating National Independent Party name...")

    # Get the National Independent Party entity directly
    national_independent_party = await context.db.get_entity(
        "entity:organization/political_party/national-independent-party"
    )

    assert (
        national_independent_party is not None
    ), "National Independent Party entity not found"

    # Update the names to make Rastriya Swatantra Party primary
    updated_names = [
        Name(
            kind=NameKind.PRIMARY,
            en=NameParts(full="Rastriya Swatantra Party (RSP)"),
            ne=NameParts(full="राष्ट्रिय स्वतन्त्र पार्टी"),
        ).model_dump(),
        Name(
            kind=NameKind.ALTERNATE,
            en=NameParts(full="National Independent Party"),
            ne=None,
        ).model_dump(),
    ]

    # Update the entity's names
    national_independent_party.names = updated_names

    await context.publication.update_entity(
        entity=national_independent_party,
        author_id=author_id,
        change_description="Update primary name to Rastriya Swatantra Party, move National Independent Party to alternate",
    )
    context.log("✓ Updated National Independent Party names")


async def migrate(context: MigrationContext) -> None:
    """
    Import remaining registered political parties from Election Commission of Nepal.
    Also update National Independent Party to use Rastriya Swatantra Party as primary name.

    Data source: parties-list.csv containing parties with registration numbers 204-230
    """
    context.log(
        "Migration started: Importing additional political parties and updating existing party names"
    )

    # Get existing author (should already exist)
    author_id = "author:damodar-dahal"
    context.log(f"Using existing author: ({author_id})")

    # STAGE 0: Update existing National Independent Party name
    context.log("Stage 0: Updating National Independent Party name...")
    await update_national_independent_party_name(context, author_id)

    # Load translated party data
    party_data = context.read_json("source/parties-data-en.json")
    context.log(f"Loaded {len(party_data)} parties from parties-data-en.json")

    # Load raw CSV for registration info
    raw_data = context.read_csv("source/parties-list.csv")

    # Create lookup by Nepali name
    raw_lookup = {row["दलको नाम"]: row for row in raw_data}

    # STAGE 1: Build all party data
    context.log("Stage 1: Building party data structures...")
    parties_to_create = []

    for name_ne, translated in party_data.items():
        raw_row = raw_lookup.get(name_ne)
        if not raw_row:
            context.log(f"WARNING: No raw data for {name_ne}")
            continue

        # Build identifiers
        identifiers = None
        reg_no = raw_row.get("दर्ता नं.")
        if reg_no:
            identifiers = [
                ExternalIdentifier(
                    scheme="other",
                    name=reg_no_external_identifier,
                    value=transliterate_to_roman(reg_no),
                )
            ]

        # Build address
        address = None
        if translated.get("address"):
            address = Address(
                description2=LangText(
                    en=LangTextValue(
                        value=translated["address"], provenance="translation_service"
                    ),
                    ne=LangTextValue(
                        value=raw_row.get("दलको मुख्य कार्यालय (ठेगाना)", ""),
                        provenance="imported",
                    ),
                )
            )

        # Build party_chief
        party_chief = None
        if translated.get("main_person"):
            party_chief = LangText(
                en=LangTextValue(
                    value=translated["main_person"], provenance="translation_service"
                ),
                ne=LangTextValue(value=raw_row.get("प्रमुख", ""), provenance="imported"),
            )

        # Build registration_date
        registration_date = None
        if raw_row.get("दल दर्ता मिति"):
            registration_date = convert_nepali_date(raw_row["दल दर्ता मिति"])

        # Build symbol
        symbol = None
        if translated.get("symbol_name"):
            symbol = PartySymbol(
                name=LangText(
                    en=LangTextValue(
                        value=translated["symbol_name"],
                        provenance="translation_service",
                    ),
                    ne=LangTextValue(
                        value=raw_row.get("चिन्हको नाम", ""), provenance="imported"
                    ),
                )
            )

        name_ne = name_extractor.standardize_name(name_ne)
        # Build names
        names = [
            Name(
                kind=NameKind.PRIMARY,
                en=NameParts(full=name_extractor.standardize_name(translated["name"])),
                ne=NameParts(full=name_ne),
            ).model_dump()
        ]

        # Create party data structure
        party_data_dict = dict(
            slug=text_to_slug(translated["name"]),
            names=names,
            attributions=[
                Attribution(
                    title=LangText(
                        en=LangTextValue(
                            value="Nepal Election Commission", provenance="human"
                        ),
                        ne=LangTextValue(value="नेपाल निर्वाचन आयोग", provenance="human"),
                    ),
                    details=LangText(
                        en=LangTextValue(
                            value=f"Registered Parties (2082) - imported {DATE}",
                            provenance="human",
                        ),
                        ne=LangTextValue(
                            value=f"दर्ता भएका दलहरू (२०८२) - आयात मिति {DATE} A.D.",
                            provenance="human",
                        ),
                    ),
                )
            ],
            identifiers=identifiers,
            address=address.model_dump() if address else None,
            party_chief=party_chief.model_dump() if party_chief else None,
            registration_date=registration_date,
            symbol=symbol.model_dump() if symbol else None,
        )

        parties_to_create.append(
            {"data": party_data_dict, "name_ne": name_ne, "name_en": translated["name"]}
        )

    context.log(f"Stage 1 complete: Prepared {len(parties_to_create)} parties")

    # STAGE 2: Check for slug collisions
    context.log("Stage 2: Checking for slug collisions...")
    # Check against existing entities
    existing_entities = await context.db.list_entities(
        limit=1000, entity_type="organization", sub_type="political_party"
    )
    existing_slugs = {entity.slug for entity in existing_entities}

    # Check for collisions
    collisions = []
    slug_counts = {}

    for party in parties_to_create:
        slug = party["data"]["slug"]

        # Check against existing entities
        if slug in existing_slugs:
            collisions.append(f"Slug '{slug}' already exists in database")

        # Check for duplicates within this migration
        if slug in slug_counts:
            slug_counts[slug] += 1
            collisions.append(f"Duplicate slug '{slug}' in migration data")
        else:
            slug_counts[slug] = 1

    if collisions:
        context.log("SLUG COLLISIONS DETECTED:")
        for collision in collisions:
            context.log(f"  - {collision}")
        raise ValueError(f"Found {len(collisions)} slug collisions. Migration aborted.")

    context.log(
        f"Stage 2 complete: No slug collisions found for {len(parties_to_create)} parties"
    )

    # STAGE 3: Commit entities to database
    context.log("Stage 3: Creating entities in database...")
    created_count = 0

    for party in parties_to_create:
        party_entity = await context.publication.create_entity(
            entity_type=EntityType.ORGANIZATION,
            entity_subtype=EntitySubType.POLITICAL_PARTY,
            entity_data=party["data"],
            author_id=author_id,
            change_description=CHANGE_DESCRIPTION,
        )
        context.log(f"Created party {party_entity.id}: {party['name_en']}")
        created_count += 1

    context.log(f"Stage 3 complete: Created {created_count} political parties")

    # Final verification
    entities = await context.db.list_entities(
        limit=1000, entity_type="organization", sub_type="political_party"
    )
    context.log(
        f"Final verification: {len(entities)} total political_party entities in database"
    )

    context.log("Migration completed successfully")
