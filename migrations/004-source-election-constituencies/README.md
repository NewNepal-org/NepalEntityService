# Migration: 004-source-election-constituencies

## Purpose

Creates election constituency entities for all 77 districts in Nepal. Each district has between 1 and 10 constituencies based on population, totaling 165 constituencies nationwide. These constituencies are used for House of Representatives (Pratinidhi Sabha) elections.

## Data Sources

- `constituencies.csv`: Contains district names (Nepali) and constituency counts
- District entities from migration 001-source-locations

## Changes

- Creates 165 constituency location entities
- Each constituency is named "{District Name} - {Number}" in both English and Nepali
- Constituencies are linked to their parent district entities
- Constituency subtype: "constituency"
- Distribution ranges from 1 constituency (e.g., Manang, Mustang) to 10 constituencies (Kathmandu)

## Notes

- Uses slug-based district matching with fallback to search when direct match fails
- DISTRICT_NAME_MAP handles variations in Devanagari spelling between CSV and database
- Processing time: approximately 0.2 seconds for 165 entities
- Migration is idempotent - can be safely re-run

## Testing

- Run migration: `nes migrate run 004-source-election-constituencies`
- Verify entity count: 165 constituencies created
- Check that all constituencies have both English and Nepali names
- Verify parent relationships link to correct districts
- Sample query: `nes search entities --type location --subtype constituency --limit 5`

## Rollback

- Delete all constituency entities: Query for `entity_type=location` and `sub_type=constituency`
- Use Git revert on the database repository commit
