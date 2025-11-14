# Migration: 005-seed-2079-election-candidates

## Purpose

Import 2079 (2022 AD) election candidates as Person entities with electoral details. This migration creates comprehensive person records including:
- Personal information (name, gender, birth date, family details)
- Electoral participation (candidacy, party affiliation, election results)
- Bilingual data (Nepali and English)

## Data Sources

- Nepal Election Commission 2079 Election Results
  - `ElectionResultCentral2079.json` - Central election results
  - `ElectionResultState2079.json` - State/Provincial election results
- Source: https://result.election.gov.np/

## Translation Process

This migration follows a two-step pattern:

1. **generate_translations.py** - Translates Nepali candidate data to English
   - Uses Google Vertex AI (Gemini) for structured translation
   - Translates names, addresses, institutions, and other text fields
   - Saves translations to `translations.json`
   - Supports incremental translation (can resume if interrupted)

2. **migrate.py** - Creates Person entities from translated data
   - Reads both raw JSON and translated data
   - Links candidates to existing political parties
   - Creates bilingual Person entities with electoral details

## Changes

- Creates 5,636 Person entities for all 2079 election candidates (central + state)
- Each person includes:
  - Primary name in both Nepali and English
  - Personal details: gender, birth date, father's name, spouse's name, address
  - Electoral details: candidacy information, party affiliation, election symbol, votes received, election status
  - Education and position information (when available)
  - External identifier linking to Nepal Election Commission candidate ID
  - Profile picture URL from election commission assets
  - Attribution to Nepal Election Commission
- Links candidates to existing political parties (from migration 003)
- Tags candidates with election-specific tags (federal/provincial candidate/elected)
- Does NOT create new political party entities (assumes they exist from previous migration)

## Results

- **Entities created**: 5,636 person entities
- **Migration duration**: 5.8 seconds
- **Versions created**: 5,636 (one per entity)
- **Relationships created**: 0 (candidates linked via party_id in electoral details)

## Notes

- Birth dates are converted from Bikram Sambat (BS) to Gregorian (AD) calendar
- Gender is parsed from Nepali text ("पुरुष" = MALE, "महिला" = FEMALE)
- Party linking uses Nepali party names to match existing entities via PARTY_ADDITIONAL_NAME_MAP
- Address data is stored as bilingual description (future migration may parse to location entities)
- Translation uses Gemini 2.5 Flash for structured data extraction
- Duplicate name slugs resolved by appending candidate ID
- Special handling for candidate ID 333804 (BP Koirala) to avoid slug collision
- Processing time: ~2-3 hours for full translation (depending on API rate limits)
- Migration execution: ~6 seconds for 5,636 entities

## Testing

Run translation first:
```bash
cd migrations/005-seed-2079-election-candidates
python generate_translations.py
```

Then run migration:
```bash
nes migrate run 005-seed-2079-election-candidates --dry-run
```

Verify:
- Check that `translations.json` is created with 5,636 translations
- Verify person count matches 5,636 candidates (5,637 total including verification)
- Check that candidates are linked to political parties via electoral_details.candidacies[0].party_id
- Review sample entities to ensure bilingual data quality
- Confirm tags are applied correctly (federal/provincial election candidates/elected)
- Validate external identifiers and picture URLs are set

## Rollback

- Use Git revert on the database repository commit
- Manually delete 5,636 created Person entities using the Publication Service
- Translation file (`translations.json`) can be regenerated if needed (contains 5,636 candidate translations)
