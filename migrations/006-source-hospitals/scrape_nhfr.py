#!/usr/bin/env python3
"""
Scrape all health facility data from Nepal Health Facility Registry (NHFR).

This script fetches all health facilities from the NHFR API and saves them
to source/hospitals.json for use by the migration.

Usage (from project root):
    cd migrations/006-source-hospitals
    poetry run python scrape_nhfr.py

Example with filters:
    poetry run python scrape_nhfr.py --filters '{"authority": 1}'
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Base URL for NHFR API
BASE_URL = "https://nhfr.mohp.gov.np/health-registry/search"


async def fetch_page(
    client: httpx.AsyncClient,
    page: int = 1,
    page_size: int = 100,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Fetch a single page of health facilities.

    Args:
        client: HTTP client
        page: Page number (1-indexed)
        page_size: Number of records per page
        filters: Optional filters to apply

    Returns:
        List of health facility records
    """
    params: Dict[str, Any] = {}

    # Add pagination params (API might ignore these if it returns all at once)
    params["page"] = page
    params["per_page"] = page_size

    # Add filters if provided
    if filters:
        params.update(filters)

    try:
        logger.info(f"Fetching page {page} (page_size={page_size})...")
        response = await client.get(BASE_URL, params=params, timeout=60.0)
        response.raise_for_status()

        data = response.json()

        # Check if data is a list (direct array response - most common)
        if isinstance(data, list):
            return data

        # Check if data is wrapped in an object with pagination info
        if isinstance(data, dict):
            # Try common pagination response formats
            if "data" in data:
                records = data["data"]
                if isinstance(records, list):
                    return records
            if "results" in data:
                records = data["results"]
                if isinstance(records, list):
                    return records
            if "items" in data:
                records = data["items"]
                if isinstance(records, list):
                    return records
            # If the dict itself contains array-like structure, return values
            if len(data) == 1 and isinstance(list(data.values())[0], list):
                return list(data.values())[0]

        logger.warning(f"Unexpected response format on page {page}: {type(data)}")
        return []

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error on page {page}: {e.response.status_code}")
        if e.response.status_code == 404:
            return []  # No more pages
        raise
    except Exception as e:
        logger.error(f"Error fetching page {page}: {e}")
        raise


async def fetch_all(
    filters: Optional[Dict[str, Any]] = None,
    page_size: int = 100,
    max_pages: Optional[int] = None,
    delay: float = 0.5,
) -> List[Dict[str, Any]]:
    """Fetch all health facilities with pagination.

    Args:
        filters: Optional filters to apply
        page_size: Number of records per page
        max_pages: Maximum number of pages to fetch (None for all)
        delay: Delay between requests in seconds

    Returns:
        List of all health facility records
    """
    all_records: List[Dict[str, Any]] = []
    page = 1
    seen_ids = set()  # Track IDs to detect duplicates

    async with httpx.AsyncClient(
        timeout=30.0,
        headers={
            "User-Agent": "Nepal Entity Service Bot/2.0 (https://github.com/yourusername/nepal-entity-service)",
            "Accept": "application/json",
        },
        follow_redirects=True,
    ) as client:
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break

            records = await fetch_page(
                client, page=page, page_size=page_size, filters=filters
            )

            if not records:
                logger.info(f"No more records found at page {page}")
                break

            # Filter out duplicates
            new_records = []
            for record in records:
                record_id = record.get("id") or record.get("hf_code")
                if record_id and record_id not in seen_ids:
                    seen_ids.add(record_id)
                    new_records.append(record)
                elif not record_id:
                    # If no ID, add anyway (might be duplicate but we can't detect)
                    new_records.append(record)

            if not new_records:
                logger.info(f"No new records at page {page}, stopping")
                break

            all_records.extend(new_records)
            logger.info(
                f"Page {page}: Got {len(new_records)} new records "
                f"(total: {len(all_records)})"
            )

            # If we got fewer records than page_size, we've reached the end
            if len(records) < page_size:
                logger.info(
                    f"Got fewer records than page_size ({len(records)} < {page_size}), reached end"
                )
                break

            # Note: The NHFR API typically returns all results in a single response
            # If we got a large number of records on the first page, it's likely all of them
            # We'll still try the next page to be safe, but if it's empty, we'll stop

            page += 1

            # Rate limiting
            if delay > 0:
                await asyncio.sleep(delay)

    return all_records


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape health facility data from NHFR API"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="source/hospitals.json",
        help="Output JSON file path (default: source/hospitals.json)",
    )
    parser.add_argument(
        "--filters",
        type=str,
        help='JSON string of filters to apply (e.g., \'{"authority": 1, "province": 1}\')',
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of records per page (default: 100)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum number of pages to fetch (default: all)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: fetch only first page",
    )

    args = parser.parse_args()

    # Parse filters
    filters = None
    if args.filters:
        try:
            filters = json.loads(args.filters)
            logger.info(f"Using filters: {filters}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in filters: {e}")
            return

    # Determine max_pages for test mode
    max_pages = 1 if args.test else args.max_pages

    logger.info("=" * 70)
    logger.info("NHFR Health Facility Scraper")
    logger.info("=" * 70)
    logger.info(f"Output file: {args.output}")
    logger.info(f"Page size: {args.page_size}")
    if filters:
        logger.info(f"Filters: {filters}")
    if max_pages:
        logger.info(f"Max pages: {max_pages}")
    logger.info("=" * 70)
    logger.info("")

    try:
        # Fetch all records
        records = await fetch_all(
            filters=filters,
            page_size=args.page_size,
            max_pages=max_pages,
            delay=args.delay,
        )

        if not records:
            logger.warning("No records fetched!")
            return

        # Save to JSON file (clean array only, no pagination metadata)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving {len(records)} records to {output_path}...")
        logger.info("Output will be a clean JSON array (no pagination metadata)")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info("")
        logger.info("=" * 70)
        logger.info("Scraping Summary")
        logger.info("=" * 70)
        logger.info(f"Total records: {len(records)}")
        logger.info(f"Output file: {output_path}")
        logger.info(f"File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        logger.info("=" * 70)

        # Print some statistics
        if records:
            # Count by type
            types = {}
            provinces = {}
            districts = {}
            for record in records:
                hf_type = record.get("healthFacilityType", {}).get(
                    "type_name", "Unknown"
                )
                types[hf_type] = types.get(hf_type, 0) + 1

                province = record.get("provinces", {}).get("nameen", "Unknown")
                provinces[province] = provinces.get(province, 0) + 1

                district = record.get("districts", {}).get("nameen", "Unknown")
                districts[district] = districts.get(district, 0) + 1

            logger.info("")
            logger.info("Statistics:")
            logger.info(f"  Types: {len(types)} different types")
            logger.info(f"  Provinces: {len(provinces)} different provinces")
            logger.info(f"  Districts: {len(districts)} different districts")
            logger.info("")
            logger.info("Top 5 types:")
            for hf_type, count in sorted(
                types.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                logger.info(f"  {hf_type}: {count}")

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
