"""
Migration: 001-source-locations
Description: This migration sources provinces, districts, and local levels including 6500+ wards.
Author: Damodar Dahal
Date: 2025-11-09
"""

import json
from urllib.request import urlopen

from nes.core.identifiers import build_entity_id
from nes.core.models import ADMINISTRATIVE_LEVELS
from nes.core.models.location import LocationType
from nes.core.models.version import Author
from nes.core.utils.devanagari import contains_devanagari
from nes.core.utils.slug_helper import text_to_slug
from nes.services.migration.context import MigrationContext

# Migration metadata (used for Git commit message)
AUTHOR = "Damodar Dahal"
DATE = "2025-11-09"
DESCRIPTION = "This migration sources provinces, districts, and local levels including 6500+ wards."
CHANGE_DESCRIPTION = "Initial sourcing"

# Data source URLs
NEPALI = "https://raw.githubusercontent.com/sagautam5/local-states-nepal/refs/heads/master/dataset/alldataset/np.json"
ENGLISH = "https://raw.githubusercontent.com/sagautam5/local-states-nepal/refs/heads/master/dataset/alldataset/en.json"

# Custom name overrides for entities with duplicate names
# Maps entity ID to (district_name_en, district_name_ne)
CUSTOM_NAME_OVERRIDES = {
    12: ("Dhankuta", "धनकुटा"),
    35: ("Sindhupalchowk", "सिन्धुपाल्चोक"),
    61: ("Dolpa", "डोल्पा"),
    68: ("Morang", "मोरङ"),
    76: ("Okhaldhunga", "ओखलढुङ्गा"),
    78: ("Panchthar", "पाँचथर"),
    89: ("Sankhuwasabha", "संखुवासभा"),
    137: ("Udayapur", "उदयपुर"),
    216: ("Siraha", "सिरहा"),
    253: ("Saptari", "सप्तरी"),
    281: ("Chitwan", "चितवन"),
    297: ("Dhading", "धादिङ"),
    332: ("Lalitpur", "ललितपुर"),
    333: ("Lalitpur", "ललितपुर"),
    335: ("Lalitpur", "ललितपुर"),
    344: ("Makawanpur", "मकवानपुर"),
    351: ("Nuwakot", "नुवाकोट"),
    374: ("Sindhuli", "सिन्धुली"),
    385: ("Sindhupalchowk", "सिन्धुपाल्चोक"),
    415: ("Kaski", "कास्की"),
    417: ("Kaski", "कास्की"),
    437: ("Myagdi", "म्याग्दी"),
    440: ("Myagdi", "म्याग्दी"),
    464: ("Syangja", "स्याङ्जा"),
    484: ("Kapilvastu", "कपिलवस्तु"),
    505: ("Rupandehi", "रुपन्देही"),
    518: ("Gulmi", "गुल्मी"),
    525: ("Gulmi", "गुल्मी"),
    527: ("Gulmi", "गुल्मी"),
    560: ("Rolpa", "रोल्पा"),
    565: ("Rolpa", "रोल्पा"),
    576: ("Banke", "बाँके"),
    588: ("Rukum", "रुकुम"),
    591: ("Rukum", "रुकुम"),
    598: ("Salyan", "सल्यान"),
    666: ("Darchula", "दार्चुला"),
    688: ("Bajura", "बाजुरा"),
    735: ("Kanchanpur", "कञ्चनपुर"),
    741: ("Kailali", "कैलाली"),
    751: ("Kailali", "कैलाली"),
}


def clean_name(name: str) -> str:
    """Clean name by removing double spaces and extra whitespace."""
    import re

    # Replace multiple spaces with single space
    return re.sub(r"\s+", " ", name.strip())


def extract_location_data(
    data_en: dict, data_ne: dict, context: MigrationContext = None
) -> tuple[list, dict, dict]:
    """Extract identifiers, attributes, and location fields from location data."""
    identifiers = []
    attributes = {}
    location_fields = {}

    # identifiers should be a list of ExternalIdentifier objects
    # Add source ID as external identifier
    source_id = data_en.get("id")
    if source_id:
        identifiers.append(
            {"scheme": "other", "value": str(source_id), "label": "Original Dataset ID"}
        )

    # Only add website if it contains no Devanagari characters
    website = data_en.get("website", "").strip()
    if website:
        if contains_devanagari(website):
            if context:
                location_name = data_en.get("name", "Unknown")
                context.log(
                    f"WARNING: Skipping invalid website with Devanagari characters for '{location_name}': {website}"
                )
        else:
            identifiers.append({"scheme": "website", "value": website, "url": website})

    if data_en.get("area_sq_km", "").strip():
        location_fields["area"] = float(data_en["area_sq_km"].strip())

    # Use LangText for headquarter
    headquarter_en = data_en.get("headquarter", "").strip()
    headquarter_ne = data_ne.get("headquarter", "").strip()
    if headquarter_en or headquarter_ne:
        headquarter = {}
        if headquarter_en:
            headquarter["en"] = {"value": headquarter_en, "provenance": "imported"}
        if headquarter_ne:
            headquarter["ne"] = {"value": headquarter_ne, "provenance": "imported"}
        attributes["headquarter"] = headquarter

    return identifiers, attributes, location_fields


def create_location_entity_data(
    name_en: str,
    name_ne: str,
    subtype: str,
    parent_id: str = None,
    identifiers: list = None,
    attributes: dict = None,
    location_fields: dict = None,
    district_slug: str = None,
    entity_id: int = None,
    district_name_en: str = None,
    district_name_ne: str = None,
    source_id: int = None,
) -> dict:
    """Create location entity data dictionary for publication service."""
    # Apply custom name overrides for specific entities
    if entity_id and entity_id in CUSTOM_NAME_OVERRIDES:
        override_district_en, override_district_ne = CUSTOM_NAME_OVERRIDES[entity_id]
        name_en = f"{name_en} ({override_district_en})"
        name_ne = f"{name_ne} ({override_district_ne})"

    slug = text_to_slug(name_en)

    names = [
        {
            "kind": "PRIMARY",
            "en": {"full": clean_name(name_en)},
            "ne": {"full": clean_name(name_ne)},
        }
    ]

    # attributions should be a list of Attribution objects with LangText
    entity_data = {
        "slug": slug,
        "type": "location",
        "sub_type": subtype,
        "names": names,
        "attributions": [
            {
                "title": {
                    "en": {"value": "Sagar Gautam (GitHub)", "provenance": "imported"}
                },
                "details": {
                    "en": {
                        "value": f"https://github.com/sagautam5/local-states-nepal (imported {DATE})",
                        "provenance": "imported",
                    }
                },
            }
        ],
    }

    # Add source ID as external identifier if provided and not already in identifiers
    if source_id and (
        not identifiers or not any(i.get("scheme") == "other" for i in identifiers)
    ):
        if not identifiers:
            identifiers = []
        identifiers.append(
            {
                "scheme": "other",
                "value": str(source_id),
                "label": "Sagar Gautam Dataset ID",
            }
        )

    if identifiers:
        entity_data["identifiers"] = identifiers
    if attributes:
        entity_data["attributes"] = attributes

    # Add location-specific fields (area, lat, lng, etc.)
    if location_fields:
        entity_data.update(location_fields)

    # parent is a direct field on Location model
    if parent_id:
        entity_data["parent"] = parent_id

    return entity_data


async def migrate(context: MigrationContext) -> None:
    """
    Parse Nepal administrative map data and create location entities.

    This migration imports the complete administrative hierarchy of Nepal:
    - 7 Provinces
    - 77 Districts
    - 700+ Local levels (municipalities and rural municipalities)
    - 6,500+ Wards

    Data is sourced from: https://github.com/sagautam5/local-states-nepal
    """
    context.log("Migration started: Importing Nepal administrative locations")

    # Create author for this migration
    author = Author(slug=text_to_slug(AUTHOR), name=AUTHOR)
    await context.db.put_author(author)
    author_id = author.id  # This will be "author:damodar-dahal"
    context.log(f"Created author: {author.name} ({author_id})")

    # Fetch data from URLs
    context.log("Fetching English data from GitHub...")
    with urlopen(ENGLISH) as response:
        english_data = json.loads(response.read())

    context.log("Fetching Nepali data from GitHub...")
    with urlopen(NEPALI) as response:
        nepali_data = json.loads(response.read())

    # Validate data consistency
    assert len(english_data) == len(nepali_data), "Province count mismatch"
    context.log(f"Loaded data for {len(english_data)} provinces")

    # Counters for reporting
    counts = {"province": 0, "district": 0, "municipality": 0, "ward": 0}

    # Category mapping for municipalities
    category_map = {
        1: "metropolitan_city",
        2: "sub_metropolitan_city",
        3: "municipality",
        4: "rural_municipality",
    }

    # Process provinces
    for province_en, province_ne in zip(english_data, nepali_data):
        assert (
            province_en["id"] == province_ne["id"]
        ), f"Province ID mismatch: {province_en['id']} != {province_ne['id']}"

        identifiers, attributes, location_fields = extract_location_data(
            province_en, province_ne, context
        )
        province_data = create_location_entity_data(
            province_en["name"],
            province_ne["name"],
            "province",
            identifiers=identifiers,
            attributes=attributes,
            location_fields=location_fields,
            source_id=province_en["id"],
        )

        await context.publication.create_entity(
            entity_data=province_data,
            author_id=author_id,
            change_description=CHANGE_DESCRIPTION,
        )
        counts["province"] += 1
        context.log(f"Created province: {province_en['name']} ({province_ne['name']})")

        province_id = build_entity_id(
            "location", "province", text_to_slug(province_en["name"])
        )

        # Process districts
        assert len(province_en["districts"]) == len(
            province_ne["districts"]
        ), f"District count mismatch in province {province_en['name']}"

        for district_en, district_ne in zip(
            province_en["districts"], province_ne["districts"]
        ):
            if isinstance(district_en, (str, int)):
                district_en = province_en["districts"][district_en]
                district_ne = province_ne["districts"][district_ne]

            assert (
                district_en["id"] == district_ne["id"]
            ), f"District ID mismatch: {district_en['id']} != {district_ne['id']}"

            identifiers, attributes, location_fields = extract_location_data(
                district_en, district_ne, context
            )
            district_data = create_location_entity_data(
                district_en["name"],
                district_ne["name"],
                "district",
                province_id,
                identifiers=identifiers,
                attributes=attributes,
                location_fields=location_fields,
                source_id=district_en["id"],
            )

            await context.publication.create_entity(
                entity_data=district_data,
                author_id=author_id,
                change_description=CHANGE_DESCRIPTION,
            )
            counts["district"] += 1

            district_slug = text_to_slug(district_en["name"])
            district_id = build_entity_id("location", "district", district_slug)

            # Process municipalities
            assert len(district_en["municipalities"]) == len(
                district_ne["municipalities"]
            ), f"Municipality count mismatch in district {district_en['name']}"

            for municipality_en, municipality_ne in zip(
                district_en["municipalities"], district_ne["municipalities"]
            ):
                if isinstance(municipality_en, (str, int)):
                    municipality_en = district_en["municipalities"][municipality_en]
                    municipality_ne = district_ne["municipalities"][municipality_ne]

                assert (
                    municipality_en["id"] == municipality_ne["id"]
                ), f"Municipality ID mismatch: {municipality_en['id']} != {municipality_ne['id']}"

                # Determine municipality type
                subtype = category_map.get(
                    municipality_en["category_id"], "municipality"
                )

                identifiers, attributes, location_fields = extract_location_data(
                    municipality_en, municipality_ne, context
                )
                municipality_data = create_location_entity_data(
                    municipality_en["name"],
                    municipality_ne["name"],
                    subtype,
                    district_id,
                    identifiers=identifiers,
                    attributes=attributes,
                    location_fields=location_fields,
                    district_slug=district_slug,
                    entity_id=municipality_en["id"],
                    district_name_en=district_en["name"],
                    district_name_ne=district_ne["name"],
                    source_id=municipality_en["id"],
                )

                await context.publication.create_entity(
                    entity_data=municipality_data,
                    author_id=author_id,
                    change_description=CHANGE_DESCRIPTION,
                )
                counts["municipality"] += 1

                # Use the actual slug from municipality_data to build the correct ID
                municipality_slug = municipality_data["slug"]
                municipality_id = build_entity_id(
                    "location", subtype, municipality_slug
                )

                # Process wards
                assert len(municipality_en["wards"]) == len(
                    municipality_ne["wards"]
                ), f"Ward mismatch in {municipality_en['name']}"

                for ward_num in municipality_en["wards"]:
                    # Use municipality slug for ward names to ensure uniqueness
                    ward_en = f"{municipality_slug} - Ward {ward_num}"
                    ward_ne = f"{municipality_ne['name'].strip()} वडा नं.– {ward_num}"

                    ward_data = create_location_entity_data(
                        ward_en, ward_ne, "ward", municipality_id
                    )

                    await context.publication.create_entity(
                        entity_data=ward_data,
                        author_id=author_id,
                        change_description=CHANGE_DESCRIPTION,
                    )
                    counts["ward"] += 1

    # Log summary
    context.log(f"Created {counts['province']} provinces")
    context.log(f"Created {counts['district']} districts")
    context.log(f"Created {counts['municipality']} municipalities")
    context.log(f"Created {counts['ward']} wards")

    # Verify counts by querying database
    for location_type in LocationType:
        entities = await context.db.list_entities(
            limit=10_000, entity_type="location", sub_type=location_type.value
        )
        context.log(
            f"Verified: {len(entities)} {location_type.value} entities in database"
        )

    context.log("Migration completed successfully")
