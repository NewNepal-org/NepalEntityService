# Migration: 001-source-locations

## Purpose

Imports Nepal administrative locations including provinces, districts, municipalities, and wards. This migration establishes the foundational geographic hierarchy for Nepal's administrative divisions with bilingual support (English and Nepali/Devanagari).

## Data Sources

- English: https://github.com/sagautam5/local-states-nepal
- Attribution: Sagar Gautam (GitHub)

## Changes

This migration creates the following entities:

- Creates 7 province entities
- Creates 77 district entities
- Creates 753 municipalities:
  - 6 metropolitan cities
  - 11 sub-metropolitan cities
  - 276 municipalities
  - 460 rural municipalities
- Creates 6,743 ward entities
- Total entities created: 7,580
- Total versions created: 7,580

## Notes

- This migration is deterministic and can be safely re-run
- Expected execution time: ~9 seconds
- Special considerations:
  - Skips invalid website URLs containing Devanagari characters (e.g., Phakphokthum Rural Municipality)
  - Includes bilingual support (English and Nepali/Devanagari)
  - No constituency entities are created in this migration
  - No relationships are created (entities only)
  - Custom name overrides applied to 13 entities with duplicate names (suffixed with district name)
  - Rural municipalities are suffixed with district slug to ensure uniqueness
  - Includes location metadata: area (sq km), headquarters, and website URLs where available
  - Ward names use municipality slug for uniqueness (e.g., "municipality-slug - Ward 1")
