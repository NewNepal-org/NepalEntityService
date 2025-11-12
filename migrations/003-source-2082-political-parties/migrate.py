"""
Migration: 002-source-political-parties
Description: Import registered political parties from Election Commission of Nepal
Author: Damodar Dahal
Date: 2025-11-11
"""

from datetime import date

from nepali_date_utils import converter

from nes.core.models import (
    Address,
    Attribution,
    Contact,
    ExternalIdentifier,
    LangText,
    LangTextValue,
    Name,
    NameParts,
    PartySymbol,
)
from nes.core.models.base import NameKind
from nes.core.models.entity import EntitySubType, EntityType
from nes.core.models.version import Author
from nes.core.utils.devanagari import transliterate_to_roman
from nes.core.utils.phone_number import normalize_nepali_phone_number
from nes.core.utils.slug_helper import text_to_slug
from nes.services.migration.context import MigrationContext
from nes.services.scraping.normalization import NameExtractor

# Migration metadata
AUTHOR = "Damodar Dahal"
DATE = "2025-11-11"
DESCRIPTION = "Import registered political parties from Election Commission of Nepal"
CHANGE_DESCRIPTION = "Initial sourcing"


# NOTE:
# Address field stores bilingual text in description.
# Future migration may parse and link to proper location entities.


name_extractor = NameExtractor()

PARTY_ADDITIONAL_NAME_MAP = {
    "जनता समाजवादी पार्टी, नेपाल": "जनता समाजवादी पार्टी, नेपाल",
    "खम्बुवान राष्ट्रिय मोर्चा नेपाल": "खम्बुवान राष्ट्रिय मोर्चा, नेपाल",
    "सचेत नेपाली पार्टी": "सचेत नेपाली पार्टी",
    "पुनर्जागरण पार्टी नेपाल": "पुनर्जागरण पार्टी, नेपाल",
    "मंगोल नेशनल अर्गनाइजेसन": "मंगोल नेशनल अर्गनाइजेशन",
    "नेपाल सद्भावना पार्टी": "राष्ट्रिय सदभावना पार्टी",
    "नेपाल कम्युनिष्ट पार्टी (एकिकृत समाजबादी)": "नेपाल कम्युनिष्ट पार्टी (एकीकृत समाजवादी)",
    "तराइ-मधेश लोकतान्त्रिक पार्टी": "तराई-मधेश लोकतान्त्रिक पार्टी",
    "लोकतान्त्रिक समाजवादी पार्टी, नेपाल": "लोकतान्त्रिक समाजवादी पार्टी नेपाल",
    "जनता प्रगतिशिल पार्टी, नेपाल": "जनता प्रगतिशील पार्टी, नेपाल",
    "नेपाल कम्युनिष्ट पार्टी (एमाले)": "नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)",
    "राष्ट्रिय मुक्ति आन्दोलन नेपाल": "राष्ट्रिय मुक्ति आन्दोलन, नेपाल",
    "नेपाल कम्युनिष्ट पार्टी (मार्क्सवादी लेनिनवादी)": "नेपाल कम्युनिष्ट पार्टी (मार्क्सवादी-लेनिनवादी)",
    "साझा पार्टी नेपाल": "साझा पार्टी, नेपाल",
    "संघीय लोकतान्त्रिक राष्ट्रिय मञ्च": "संघीय लोकतान्त्रिक राष्ट्रिय मत",
    "जनसमाजवादी पार्टी नेपाल": "जनसमाजवादी पार्टी, नेपाल",
    "किरात खम्बुवान साझा पार्टी": "राष्ट्रिय साझा पार्टी",  # Name change (https://khabarhub.com/2024/03/614376/)
    "आमूल परिवर्तन मसिहा पार्टी नेपाल": "आमूल परिवर्तन रिपब्लिकन पार्टी नेपाल",  # Name change (https://khabarhub.com/2024/03/614376/)
    "तामाङसालिङ लोकतान्त्रिक पार्टी": "जनप्रिय लोकतान्त्रिक पार्टी",  # Name change (https://khabarhub.com/2024/03/614376/)
    "पिछडावर्ग निषाद दलित जनजाती पार्टी": "विकासशील जनता पार्टी",  # Both are located in Morang
    "एकीकृत शक्ति नेपाल": "नागरिक शक्ति, नेपाल",  # Both led by देवप्रकाश त्रिपाठी
    "नेपाल सुशासन पार्टी": "राष्ट्रिय मातृभूमि पार्टी",  # United with Nepal Aama Party: https://kendrabindu.com/politics/127308/
    "नेपाल आमा पार्टी": "राष्ट्रिय मातृभूमि पार्टी",  # United with Nepal Sushasan Party
    "नेपाल दलित पार्टी": "नेपाल मानवतावादी पार्टी",  # both led by मेघ बहादुर कामी
    "नेपाल समाजवादी पार्टी": "नेपाल कम्युनिष्ट पार्टी (माओवादी केन्द्र)",  # फणीन्द्र देवकोटा is a member of Maobadi
    "संघीय लोकतान्त्रिक राष्ट्रिय मञ्च(थरुहट)": "संघीय नेपाल पार्टी",  # same election symbol "gagri"
    "सामाजिक एकता पार्टी": "संयुक्त नागरिक पार्टी",  # Both have guitar election symbol.
    "इतिहासिक प्रजातान्त्रिक जनता पार्टी नेपाल": "इतिहासिक जनता पार्टी",  # Both have tractor election symbol.
}

# Reverse map: corrected name -> original name
PARTY_ADDITIONAL_NAME_MAP_REVERSE = {
    name_extractor.standardize_name(v): name_extractor.standardize_name(k)
    for k, v in PARTY_ADDITIONAL_NAME_MAP.items()
}


def convert_nepali_date(date_str: str) -> date:
    """Convert Nepali date to date object."""
    date_roman = transliterate_to_roman(date_str)
    y, m, d = date_roman.split("-")
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


async def migrate(context: MigrationContext) -> None:
    """
    Import registered political parties from Election Commission of Nepal.

    Data source: Registered Parties (2082).pdf from Election Commission
    """
    context.log("Migration started: Importing political parties")

    # Create author
    author = Author(slug=text_to_slug(AUTHOR), name=AUTHOR)
    await context.db.put_author(author)
    author_id = author.id
    context.log(f"Created author: {author.name} ({author_id})")

    # Load translated party data
    party_data = context.read_json("source/parties-data-en.json")
    context.log(f"Loaded {len(party_data)} parties from parties-data-en.json")

    # Load raw CSV for registration info
    raw_data = context.read_csv("source/parties-2082.csv", delimiter="|")

    # Create lookup by Nepali name
    raw_lookup = {row["दलको नाम"]: row for row in raw_data}

    count = 0
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
                description=f"{translated['address']} / {raw_row.get('दलको मुख्य कार्यालय (ठेगाना)', '')}"
            )

        # Build party_chief
        party_chief = None
        if translated.get("main_person"):
            party_chief = LangText(
                en=LangTextValue(
                    value=translated["main_person"], provenance="translation_service"
                ),
                ne=LangTextValue(
                    value=raw_row.get("प्रमुख पदाधिकारीको नाम", ""), provenance="imported"
                ),
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

        # Build contacts
        contacts = None
        if translated.get("contact"):
            contacts = [
                Contact(type="PHONE", value=normalize_nepali_phone_number(phone))
                for phone in translated["contact"]
                if phone
            ]

        name_ne = name_extractor.standardize_name(name_ne)
        # Build names (primary + additional if found in reverse map)
        names = [
            Name(
                kind=NameKind.PRIMARY,
                en=NameParts(full=name_extractor.standardize_name(translated["name"])),
                ne=NameParts(full=name_ne),
            ).model_dump()
        ]
        if name_ne in PARTY_ADDITIONAL_NAME_MAP_REVERSE:
            original_name = PARTY_ADDITIONAL_NAME_MAP_REVERSE[name_ne]
            names.append(
                Name(
                    kind=NameKind.ALTERNATE,
                    ne=NameParts(full=original_name),
                ).model_dump()
            )

        # Create entity
        party_data = dict(
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
            contacts=contacts,
            address=address.model_dump() if address else None,
            party_chief=party_chief.model_dump() if party_chief else None,
            registration_date=registration_date,
            symbol=symbol.model_dump() if symbol else None,
        )

        party = await context.publication.create_entity(
            entity_type=EntityType.ORGANIZATION,
            entity_subtype=EntitySubType.POLITICAL_PARTY,
            entity_data=party_data,
            author_id=author_id,
            change_description=CHANGE_DESCRIPTION,
        )
        context.log(f"Created party {party.id}")

        count += 1

    context.log(f"Created {count} political parties")

    # Verify
    entities = await context.db.list_entities(
        limit=1000, entity_type="organization", sub_type="political_party"
    )
    context.log(f"Verified: {len(entities)} political_party entities in database")

    context.log("Migration completed successfully")
