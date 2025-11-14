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

- Creates Person entities for all 2079 election candidates (central + state)
- Each person includes:
  - Primary name in both Nepali and English
  - Personal details: gender, birth date, father's name, spouse's name, address
  - Electoral details: candidacy information, party affiliation, election symbol, votes received, election status
  - Attribution to Nepal Election Commission
- Links candidates to existing political parties (from migration 003)
- Does NOT create new political party entities (assumes they exist from previous migration)

## Notes

- Birth dates are converted from Bikram Sambat (BS) to Gregorian (AD) calendar
- Gender is parsed from Nepali text ("पुरुष" = MALE, "महिला" = FEMALE)
- Party linking uses Nepali party names to match existing entities
- Address data is stored as bilingual description (future migration may parse to location entities)
- Translation uses Gemini 2.0 Flash for cost-effectiveness
- Processing time: ~2-3 hours for full translation (depending on API rate limits)
- Migration execution: ~5-10 minutes

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
- Check that `translations.json` is created with translations
- Verify person count matches expected number of candidates
- Check that candidates are linked to political parties
- Review sample entities to ensure data quality

## Rollback

- Use Git revert on the database repository commit
- Manually delete created Person entities using the Publication Service
- Translation file (`translations.json`) can be regenerated if needed
