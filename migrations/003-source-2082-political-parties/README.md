# Migration: 003-source-2082-political-parties

## Purpose

Import registered political parties from the Nepal Election Commission's official registry as of 2082 BS (Kartik 2). This migration establishes the foundational database of all legally registered political parties in Nepal with their official registration details, contact information, and party leadership.

## Data Sources

- **Primary Source**: Nepal Election Commission - "Registered Parties (2082).pdf" (NEC - Parties - 2082 Kartik 2.pdf)
- **Processed Data**: 
  - `source/parties-2082.csv` - Extracted and structured data from the PDF
  - `source/parties-data-en.json` - English translations of party names, addresses, and other fields generated via translation service
- **Data Provenance**: Official government registry from Nepal Election Commission

## Changes

- Creates 124 political party entities (organization/political_party type)
- Each party includes:
  - Bilingual names (Nepali Devanagari and English)
  - Election Commission registration number (external identifier)
  - Registration date (converted from Nepali BS to Gregorian calendar)
  - Party headquarters address (bilingual)
  - Contact phone numbers (normalized)
  - Party chief/main official name (bilingual)
  - Electoral symbol name (bilingual)
- Attribution to Nepal Election Commission as the data source
- All entities versioned with author "Damodar Dahal" and change description "Initial sourcing"

## Notes

- Processing time: approximately 0.1 seconds for 124 entities
- English translations were generated using a translation service and marked with provenance="translation_service"
- Nepali source data marked with provenance="imported"
- Phone numbers normalized to standard format using normalize_nepali_phone_number utility
- Dates converted from Nepali BS calendar to ISO format (Gregorian)
- Some parties have missing data fields (empty symbol names, no contact info) - preserved as-is from source
- Address field currently stored as attribute; may need resolution to proper location entities in future migration

## Testing

- Run migration: `nes migrate run 003-source-2082-political-parties`
- Verify entity count: Should create exactly 124 political_party entities
- Check bilingual names: All parties should have both Nepali and English names
- Verify registration numbers: Check that external identifiers are present for parties with registration numbers
- Sample verification: Review major parties like "Nepali Congress", "CPN-UML", "CPN (Maoist Centre)" for data accuracy
- Check date conversion: Verify registration dates are properly converted to ISO format

## Rollback

- Use Git revert on the database repository commit created by this migration
- Manually delete the 124 political_party entities using the Publication Service
- Filter by attribution source "Nepal Election Commission" and date "2025-11-11" to identify entities from this migration
