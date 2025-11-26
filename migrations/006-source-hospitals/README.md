# Migration 006: Import Nepal Hospitals from NHFR

## Purpose

Import hospital and health facility data from Nepal Health Facility Registry (NHFR) at https://nhfr.mohp.gov.np/

## Data Source

- **Primary Source**: Nepal Health Facility Registry API (https://nhfr.mohp.gov.np/health-registry/search)
- **Authority**: Ministry of Health and Population, Nepal
- **Data Type**: Government and non-government health facilities

## Two-Step Process

This migration uses a two-step approach:

### Step 1: Scrape Data

Run the scraping script to fetch all health facilities from NHFR API and save to `source/hospitals.json`:

**Option 1: From the migration directory (recommended)**
```bash
cd migrations/006-source-hospitals
poetry run python scrape_nhfr.py
```

**Option 2: From project root**
```bash
poetry run python migrations/006-source-hospitals/scrape_nhfr.py
```

**With filters (optional):**
```bash
# Only government facilities
cd migrations/006-source-hospitals
poetry run python scrape_nhfr.py --filters '{"authority": 1}'

# Government facilities in Bagmati Province
poetry run python scrape_nhfr.py --filters '{"authority": 1, "province": 3}'
```

**Note:** The script saves data to `source/hospitals.json` within the migration directory. If you already have scraped data, you can skip this step and proceed directly to Step 2.

**Available filters:**
- `authority`: 1 (Government) or other values (Non-Government)
- `province`: Province ID (1-7)
- `district`: District ID
- `palika`: Municipality ID
- `type`: Facility type ID
- `service`: Service type ID

### Step 2: Run Migration

After scraping, run the migration to import the data into the entity database:

**From project root:**
```bash
poetry run nes migration run 006-source-hospitals
```

**Note:** Make sure `source/hospitals.json` exists in the migration directory before running the migration. If the file is missing, the migration will fail with a clear error message.

## What Gets Created

For each health facility:

1. **Organization Entity** (type: hospital)
   - Bilingual names (English and Nepali where available)
   - External identifiers (NHFR facility code)
   - Address with location linking
   - Description (if available)
   - Attributes:
     - `beds`: Number of beds (if available)
     - `services`: List of services provided
     - `ownership`: Government/Public/Private
     - `facility_type`: Type of health facility
     - `facility_level`: Level of care provided

2. **LOCATED_IN Relationships**
   - Links to district/municipality entities
   - Links to province entities

## Data Normalization

The migration performs the following normalization:

1. **Names**: Standardizes facility names, handles bilingual content
2. **Ownership**: Normalizes to "Government", "Public", or "Private"
3. **Location**: Links to existing location entities in the database
4. **Addresses**: Constructs address from district, municipality, ward info

## Testing

After running the migration:

```bash
# Check hospital count
poetry run nes entity list --type organization --sub-type hospital

# View a sample hospital
poetry run nes entity get <hospital-id>

# Check relationships
poetry run nes entity relationships <hospital-id>
```

## Notes

- The NHFR API returns all results in a single response (no actual pagination)
- The scraping script handles deduplication automatically
- Facilities without names are skipped
- Location matching uses fuzzy search to link to existing location entities
- Some facilities may not have all attributes (beds, services, etc.)

## Rollback

To rollback this migration:

```bash
poetry run nes migration rollback 006-source-hospitals
```

This will remove all hospital entities and relationships created by this migration.

## File Structure

```
migrations/006-source-hospitals/
├── migrate.py          # Main migration script
├── scrape_nhfr.py      # Scraping script (run this first)
├── README.md           # This file
└── source/
    └── hospitals.json  # Scraped data (created by scrape_nhfr.py)
```

**Important:** The scraping script (`scrape_nhfr.py`) is located **inside** the migration directory, not in a `scripts/` folder. Always run it from the migration directory or use the full path.

## Statistics (Expected)

- **Total facilities**: ~11,000+
- **Government facilities**: ~8,900+
- **Non-government facilities**: ~2,500+
- **Provinces covered**: All 7 provinces
- **Districts covered**: All 77 districts
