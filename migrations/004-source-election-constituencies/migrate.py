"""
Migration: 004-source-election-constituencies
Description: Creates 165 election constituency entities across Nepal's 77 districts.
             Each constituency is a location entity linked to its parent district.
Author: Damodar Dahal
Date: 2025-11-12
"""

from nes.core.identifiers import build_entity_id
from nes.core.models.entity import EntitySubType, EntityType
from nes.core.models.version import Author
from nes.core.utils.slug_helper import text_to_slug
from nes.services.migration.context import MigrationContext

# Migration metadata
AUTHOR = "Damodar Dahal"
DATE = "2025-11-12"
DESCRIPTION = "Create election constituency entities for all districts."
CHANGE_DESCRIPTION = "Add election constituencies."

# CSV to database district name mapping
DISTRICT_NAME_MAP = {
    "अर्घाखांची": "arghakhanchi",
    "कन्चनपुर": "kanchanpur",
    "काठमाडौं": "kathmandu",
    "काभ्रेपलाञ्चोक": "kavrepalanchok",
    "खोटाङ्ग": "khotang",
    "तेर्हथुम": "terhathum",
    "धादिङ्ग": "dhading",
    "नवलपरासी (बर्दघाट सुस्ता पश्चिम)": "parasi",
    "नवलपरासी (बर्दघाट सुस्ता पूर्व)": "nawalpur",
    "पाँचथर": "pachthar",
    "प्यूठान": "pyuthan",
    "बझाङ्ग": "bajhang",
    "मनाङ्ग": "manang",
    "मुस्तांग": "mustang",
    "मोरङ्ग": "morang",
    "रुकुम पूर्व": "eastern-rukum",
    "लमजुंग": "lamjung",
    "सोलुखुम्बु": "solukhumbu",
    "स्याङ्जा": "syangja",
}


async def migrate(context: MigrationContext) -> None:
    """
    Create election constituency entities for all districts.

    Reads constituencies.csv which maps each district to its number of constituencies.
    Creates location entities with subtype 'constituency', named '{District} - {Number}'.
    Uses slug-based matching with DISTRICT_NAME_MAP for CSV-to-database name variations.
    Falls back to search when direct slug match fails.

    Results: 165 constituencies created across 77 districts (1-10 per district).
    """
    context.log("Migration started: Creating election constituencies")

    # Create author
    author = Author(slug=text_to_slug(AUTHOR), name=AUTHOR)
    await context.db.put_author(author)
    author_id = author.id
    context.log(f"Created author: {author.name} ({author_id})")

    # Read constituency data
    data = context.read_csv("constituencies.csv")
    context.log(f"Loaded {len(data)} districts from CSV")

    # Get all districts from database
    districts = await context.db.list_entities(
        limit=10_000, entity_type="location", sub_type="district"
    )
    district_map = {district.slug: district for district in districts}

    total_constituencies = 0

    # Process each district
    for row in data:
        district_name_ne = row["DistrictName"]
        num_constituencies = int(row["SCConstID"])

        # Apply slug mapping or convert to slug
        district_slug = DISTRICT_NAME_MAP.get(
            district_name_ne, text_to_slug(district_name_ne)
        )
        district = district_map.get(district_slug)

        # If direct match fails, search for district
        if not district:
            results = await context.search.search_entities(
                query=district_name_ne,
                entity_type="location",
                sub_type="district",
                limit=1,
            )
            district = results[0] if results else None

        if not district:
            context.log(f"WARNING: District not found: {district_name_ne}")
            continue

        del district_map[district.slug]

        district_name_en = (
            district.names[0].en.full if district.names[0].en else district_name_ne
        )

        # Create constituencies for this district
        for const_num in range(1, num_constituencies + 1):
            name_en = f"{district_name_en} - {const_num}"
            name_ne = f"{district_name_ne} - {const_num}"

            constituency_data = {
                "slug": text_to_slug(name_en),
                "names": [
                    {
                        "kind": "PRIMARY",
                        "en": {"full": name_en},
                        "ne": {"full": name_ne},
                    }
                ],
                "parent": district.id,
            }

            await context.publication.create_entity(
                entity_type=EntityType.LOCATION,
                entity_subtype=EntitySubType.CONSTITUENCY,
                entity_data=constituency_data,
                author_id=author_id,
                change_description=CHANGE_DESCRIPTION,
            )
            total_constituencies += 1

    assert len(district_map) == 0, "All districts must've been used up."

    context.log(f"Created {total_constituencies} constituencies")
    context.log("Migration completed successfully")
