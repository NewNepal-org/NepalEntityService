# Migration 002: Ward Name Fix

**Author:** Damodar Dahal  
**Date:** 2025-11-11

## Description

Fixes ward entity names by properly formatting the parent municipality/rural municipality name. The migration updates all ward entities that have hyphenated parent names in their English full name, replacing them with properly capitalized parent names.

## Changes

- Searches all ward entities (location type with sub_type "ward")
- Identifies wards with hyphenated names (e.g., "aadarsha-rural-municipality - Ward 1")
- Retrieves the parent entity's proper name
- Updates the ward's English full name to use the parent's properly formatted name (e.g., "Aadarsha Rural Municipality - Ward 1")

## Example

**Before:**
```
"aadarsha-rural-municipality - Ward 1"
```

**After:**
```
"Aadarsha Rural Municipality - Ward 1"
```

## Impact

- Affects all ward entities with hyphenated parent names
- Creates new version (version 2) for each updated ward entity
- Improves consistency and readability of ward names
