# Migration 007: Redact Family Information

## Purpose

This migration removes family information from all person entities for privacy reasons. The organization has decided not to keep this information in the database.

## Changes

This migration updates all person entities by truncating the following fields in `PersonDetails`:
- `spouse_name`
- `mother_name`
- `father_name`

These fields are set to `None` if they currently have values.

## Data Sources

No external data sources. This migration processes existing entities in the database.

## Dependencies

None. This migration operates on existing person entities.

## Impact

All person entities with family information will have those fields removed. This is a permanent change that removes sensitive personal information.

## Notes

- This migration follows the pattern from 002-ward-name-fix for updating existing entities
- Only person entities with PersonDetails containing the family fields will be updated
- The migration uses the publication service to ensure proper versioning and tracking of changes
