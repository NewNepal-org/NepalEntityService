"""
World Bank Data Scraper for Nepal Development Projects.

This module provides functionality to crawl and extract project data from
the World Bank's APIs for projects related to Nepal. It follows the existing
architecture patterns in the nes project and implements proper rate limiting,
error handling, and data normalization.

The scraper targets the following World Bank APIs:
1. World Bank Projects & Operations API: https://search.worldbank.org/api/v3/projects
2. FinancesOne API: https://datacatalogapi.worldbank.org/dexapps/fone/summary/ibrd/lending/table
3. World Bank Open API: https://api.worldbank.org/v2/projects
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp

from nes.services.scraping.web_scraper import RateLimiter, RetryHandler

# Configure logging
logger = logging.getLogger(__name__)


class WorldBankAPIClient:
    """HTTP client for World Bank APIs with rate limiting and retry logic."""

    def __init__(
        self,
        requests_per_second: float = 0.5,  # Conservative rate limit
        requests_per_minute: int = 30,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """Initialize the World Bank API client.

        Args:
            requests_per_second: Maximum requests per second per domain
            requests_per_minute: Maximum requests per minute per domain
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            requests_per_minute=requests_per_minute,
        )
        self.retry_handler = RetryHandler(max_retries=max_retries)
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "User-Agent": "Nepal-Development-Project-Service/1.0",
                "Accept": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self, url: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make a request to the World Bank API with rate limiting and error handling.

        Args:
            url: The API endpoint URL
            params: Query parameters for the request

        Returns:
            JSON response data or None if request fails
        """
        if not self.session:
            raise RuntimeError(
                "Client not initialized. Use within async context manager."
            )

        # Apply rate limiting
        await self.rate_limiter.acquire("worldbank.org")

        # Prepare URL with parameters
        if params:
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        try:
            # Use browser-like headers to mimic web requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            }

            async with self.session.get(full_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"API request failed with status {response.status}: {full_url}"
                    )
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for URL: {full_url}")
            return None
        except Exception as e:
            logger.error(f"Error making request to {full_url}: {e}")
            return None


class WorldBankProjectScraper:
    """Scraper for World Bank projects related to Nepal."""

    # Main API endpoints
    PROJECT_API_URL = "https://search.worldbank.org/api/v3/projects"
    FINANCESONE_API_URL = (
        "https://datacatalogapi.worldbank.org/dexapps/fone/summary/ibrd/lending/table"
    )
    OPEN_API_URL = "https://api.worldbank.org/v2/projects"

    def __init__(self, client: Optional[WorldBankAPIClient] = None):
        """Initialize the World Bank project scraper.

        Args:
            client: WorldBankAPIClient instance. If None, a default client will be created
        """
        self.client = client or WorldBankAPIClient()
        self.nepal_country_code = "NP"  # Nepal country code used by World Bank

    async def search_nepal_projects(
        self, fiscal_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for World Bank projects related to Nepal.

        Args:
            fiscal_year: Optional fiscal year to filter projects

        Returns:
            List of project data dictionaries
        """
        async with self.client:
            # Method 1: Using World Bank Projects & Operations API
            projects = await self._fetch_projects_from_main_api(fiscal_year)

            # Method 2: Using FinancesOne API for additional data
            finances_data = await self._fetch_from_financesone_api()

            # Combine and deduplicate data
            combined_projects = self._combine_and_deduplicate(projects, finances_data)

            logger.info(
                f"Successfully scraped {len(combined_projects)} projects for Nepal"
            )
            return combined_projects

    async def _fetch_projects_from_main_api(
        self, fiscal_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch projects from World Bank Projects & Operations API.

        Args:
            fiscal_year: Optional fiscal year to filter projects

        Returns:
            List of project data dictionaries
        """
        # Use the v3 API with appropriate parameters - more specific for Nepal projects only
        search_url = "https://search.worldbank.org/api/v3/projects"
        params = {
            "format": "json",
            "countrycode_exact": self.nepal_country_code,  # More specific exact match
            "rows": 1000,  # Fetch up to 1000 projects
            "fl": "id,proj_id,projectnumber,projectname,projectstatus,impagency,boardapprovaldate,closingdate,grantamt,ibrdamt,totalamt,envassesmentcategorycode,url,doctyperestricted,implementing_agency,sector,sector1,sector2,sector3,sector4,sector5,sector6,theme1,theme2,theme3,theme4,status,approval_date,project_name,recent_prod,lineofcreditarramt,country_name,countryshortname,regionname,envassesmentcategorycode,productlinetype,prodlinetext,totalcommamt,curr_project_cost,ibrdcommitment,idacommitment,grant_amount,loan_amount,project_abstract,borrower,major_sectors,countryhomepageurl,regionhomepageurl,major_sector_name,major_sector_code,mjsector,themev2_level1_exact,themev2_level2_exact,theme_exact,status_exact,esrc_ovrl_risk_rate,countrycode",
        }

        if fiscal_year:
            # Note: The exact parameter name may vary depending on the API
            # This is based on common patterns
            params["fiscal_year"] = fiscal_year

        try:
            data = await self.client._make_request(search_url, params)
            # Check if the response is valid before processing
            if data is None:
                logger.warning(f"Received None response from API")
                return []
            if isinstance(data, int):
                logger.warning(
                    f"Received integer response from API (likely status code): {data}"
                )
                return []
            if isinstance(data, dict):
                # Handle the actual response format from the search API you provided
                # The projects are in data["projects"] as a map of project_id -> project_data
                if "projects" in data and isinstance(data["projects"], dict):
                    # Convert the project map to a list of project data
                    projects_list = list(data["projects"].values())

                    # Filter to only include projects that are actually for Nepal
                    # Check country code and country name to make sure
                    nepal_projects = []
                    for project in projects_list:
                        country_code = project.get("countrycode", [])
                        country_name = project.get("countryname", "")
                        country_short = project.get("countryshortname", "")

                        # More strict check - must be Nepal and NOT be another country
                        # Ensure the project is for Nepal and not just mentioning Nepal somewhere
                        is_nepal = (
                            (
                                self.nepal_country_code in country_code
                                if isinstance(country_code, list)
                                else self.nepal_country_code == country_code
                            )
                            or self.nepal_country_code in str(country_code)
                            or "Nepal" in country_name
                            or "Nepal" in country_short
                        )

                        # Additional check: exclude if it's clearly another country (like Liberia, India, etc.)
                        is_other_country = (
                            "Liberia" in country_name
                            or "Liberia" in country_short
                            or "India" in country_name
                            or "India" in country_short
                            or "Sri Lanka" in country_name
                            or "Sri Lanka" in country_short
                            or "Bangladesh" in country_name
                            or "Bangladesh" in country_short
                            or "Pakistan" in country_name
                            or "Pakistan" in country_short
                            or "Myanmar" in country_name
                            or "Myanmar" in country_short
                            or "Bhutan" in country_name
                            or "Bhutan" in country_short
                            or "Afghanistan" in country_name
                            or "Afghanistan" in country_short
                            or "Nigeria" in country_name
                            or "Nigeria" in country_short
                            or "Ghana" in country_name
                            or "Ghana" in country_short
                        )

                        # Only include if it's Nepal and not clearly another country
                        if is_nepal and not is_other_country:
                            nepal_projects.append(project)
                        elif is_nepal and is_other_country:
                            logger.debug(
                                f"Excluding project {project.get('id', 'unknown')} - appears to be for another country despite Nepal filter"
                            )

                    logger.info(
                        f"Filtered to {len(nepal_projects)} projects actually for Nepal out of {len(projects_list)} total projects"
                    )
                    return nepal_projects
                elif "documents" in data:
                    return data["documents"]
                elif "rows" in data:
                    return data["rows"]
                elif "source" in data and "rows" in data.get("source", {}):
                    return data["source"]["rows"]
                elif (
                    "total_rows" in data and "rows" in data
                ):  # Common API response format
                    return data["rows"]
                else:
                    # Return the entire response as a single item if it contains project data
                    return [data] if data else []
            elif isinstance(data, list):
                return data
            else:
                logger.warning(
                    f"Received unexpected response type from API: {type(data)}"
                )
                return []
        except Exception as e:
            logger.error(f"Error fetching projects from main API: {e}")
            return []

    async def _fetch_from_financesone_api(self) -> List[Dict[str, Any]]:
        """Fetch lending data from FinancesOne API.

        This API requires a POST request with specific parameters
        based on the example provided in the requirements.

        Returns:
            List of lending data dictionaries
        """
        # Based on the example POST request provided in the requirements
        post_data = {
            "country_code": self.nepal_country_code,
            "CountryCode": self.nepal_country_code,  # Using both formats to ensure it works
            "report_type": "IBRD",
            "fiscal_year": "All Years",  # Could be parameterized
        }

        # Use headers that match the example request from your requirements
        # Without subscription key as requested
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Origin": "https://financesone.worldbank.org",
            "Pragma": "no-cache",
            "Referer": "https://financesone.worldbank.org/",
            "Sec-Ch-Ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        try:
            # Since this is a POST request, we'll need to make a direct request
            # rather than using the standard client method
            await self.client.rate_limiter.acquire("datacatalogapi.worldbank.org")

            async with self.client.session.post(
                self.FINANCESONE_API_URL, json=post_data, headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Process and return the lending data
                    return self._process_financesone_data(data)
                else:
                    logger.warning(
                        f"FinancesOne API request failed with status {response.status}"
                    )
                    return []
        except Exception as e:
            logger.error(f"Error fetching data from FinancesOne API: {e}")
            return []

    def _process_financesone_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw FinancesOne API response data.

        Args:
            data: Raw response from FinancesOne API

        Returns:
            List of processed lending data
        """
        # Based on the sample response you provided
        processed_data = []

        if isinstance(data, dict):
            if "LendingGridData" in data:
                # Process the actual lending data array
                lending_items = data["LendingGridData"]
            elif isinstance(data.get("LendingGridData"), list):
                # Handle case where data is nested differently
                lending_items = data["LendingGridData"]
            else:
                # Fallback to the top-level data if it's a single item
                lending_items = [data]
        elif isinstance(data, list):
            # If it's already a list of lending items
            lending_items = data
        else:
            # If data is neither dict nor list, create a single-item list
            lending_items = [data] if data else []

        for item in lending_items:
            if isinstance(item, dict):
                # Check if this item is for Nepal before processing
                country_name = item.get("CountryName", "")
                country_code = item.get("CountryCode", item.get("countrycode", ""))

                # Only include items that are for Nepal
                if country_code == self.nepal_country_code or "Nepal" in country_name:
                    processed_item = {
                        "project_id": item.get(
                            "ProjectId", item.get("project_id", item.get("id", ""))
                        ),
                        "project_name": item.get(
                            "ProjectName",
                            item.get("project_name", item.get("name", "")),
                        ),
                        "lending_instrument": item.get(
                            "Product", item.get("lending_instrument", "")
                        ),
                        "loan_amount": item.get(
                            "Principal", item.get("loan_amount", item.get("amount", ""))
                        ),
                        "grant_amount": item.get("grant_amount", ""),
                        "status": item.get("Status", item.get("status", "")),
                        "fiscal_year": item.get(
                            "FiscalYear", item.get("fiscal_year", item.get("year", ""))
                        ),
                        "sector": item.get("sector", ""),
                        "implementing_agency": item.get("implementing_agency", ""),
                        "borrower": item.get("Borrower", item.get("borrower", "")),
                        "closing_date": item.get(
                            "ClosedDate", item.get("closing_date", "")
                        ),
                        "disbursement": item.get(
                            "Disbursed", item.get("disbursement", "")
                        ),
                        "repayment_commencement_date": item.get(
                            "repayment_commencement_date", ""
                        ),
                        "last_repayment_date": item.get("last_repayment_date", ""),
                        "approval_date": item.get("ApprovalDate", ""),
                        "country": item.get("CountryName", ""),
                        "region": item.get("RegionName", ""),
                        "available_amount": item.get("Available", ""),
                        "borrower_obligation": item.get("BorrowerObligation", ""),
                    }
                    processed_data.append(processed_item)

        return processed_data

    def _combine_and_deduplicate(
        self, projects: List[Dict[str, Any]], finances_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine data from different APIs and remove duplicates.

        Args:
            projects: Projects from main API
            finances_data: Lending data from FinancesOne API

        Returns:
            Combined list of unique projects
        """
        # Create a dict with unique identifiers as keys to avoid duplicates
        combined_projects = {}

        # Add projects from main API
        for project in projects:
            project_id = project.get("project_id", project.get("id", ""))
            if project_id:
                combined_projects[project_id] = project

        # Add or merge data from FinancesOne API
        for finance_item in finances_data:
            project_id = finance_item.get("project_id", "")
            if project_id and project_id not in combined_projects:
                # Add as new project if not exists
                combined_projects[project_id] = finance_item
            elif project_id in combined_projects:
                # Merge data if project already exists
                combined_projects[project_id].update(finance_item)

        return list(combined_projects.values())

    def normalize_project_data(self, raw_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt raw World Bank project data to the nes.core.models.project.Project schema.
        Returns a dict compatible with Project using the new FinancingCommitment format.
        """
        # --- ID and core fields ---
        donor_project_id = (
            raw_project.get("project_id")
            or raw_project.get("proj_id")
            or raw_project.get("id")
            or raw_project.get("projectnumber")
            or None
        )
        title = raw_project.get("project_name") or raw_project.get("projectname") or ""
        description = (
            raw_project.get("project_abstract") or raw_project.get("description") or ""
        )
        # --- Status/stage ---
        status_map = {
            "Pipeline": "pipeline",
            "Planning": "planning",
            "Proposed": "planning",
            "Active": "ongoing",
            "Ongoing": "ongoing",
            "Approved": "approved",
            "Signed": "approved",
            "Closed": "completed",
            "Completed": "completed",
            "Canceled": "cancelled",
            "Cancelled": "cancelled",
            "Dropped": "terminated",
        }
        wb_status = (
            raw_project.get("status")
            or raw_project.get("projectstatus")
            or raw_project.get("status_exact")
            or ""
        )
        if isinstance(wb_status, list):
            wb_status = wb_status[0] if wb_status else ""
        stage = status_map.get(str(wb_status).strip(), "unknown")
        # --- Agencies ---
        implementing_agency = (
            raw_project.get("implementing_agency")
            or raw_project.get("impagency")
            or None
        )
        executing_agency = raw_project.get("executing_agency") or None
        # --- Financing (new FinancingCommitment format) ---
        financing_commitments = []

        def parse_float(val):
            try:
                if val is None:
                    return None
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    return float(val.replace(",", "").replace(" USD", ""))
            except Exception:
                return None

        loan_amt = (
            raw_project.get("loan_amount")
            or raw_project.get("ibrdamt")
            or raw_project.get("ibrd_amount")
            or raw_project.get("ibrdcommitment")
        )
        grant_amt = raw_project.get("grant_amount") or raw_project.get("grantamt")
        total_amt = (
            raw_project.get("totalamt")
            or raw_project.get("totalcommamt")
            or raw_project.get("total_amount")
        )
        currency = "USD"

        # Parse approval date for transaction_date
        approval_date_raw = (
            raw_project.get("board_approval_date")
            or raw_project.get("boardapprovaldate")
            or raw_project.get("approval_date")
        )
        transaction_date = None
        if approval_date_raw:
            try:
                if "T" in str(approval_date_raw):
                    transaction_date = str(approval_date_raw).split("T")[0]
                else:
                    transaction_date = str(approval_date_raw)[:10]
            except Exception:
                pass

        # Create FinancingCommitment entries (new schema with donor at top level)
        if loan_amt and parse_float(loan_amt):
            financing_commitments.append(
                {
                    "donor": "World Bank",
                    "amount": parse_float(loan_amt),
                    "currency": currency,
                    "assistance_type": "loan",
                    "financing_instrument": "IBRD Loan",
                    "budget_type": "on_budget",
                    "terms": None,
                    "transaction_date": transaction_date,
                    "transaction_type": "commitment",
                    "is_actual": True,
                    "source": "WB",
                }
            )
        if grant_amt and parse_float(grant_amt):
            financing_commitments.append(
                {
                    "donor": "World Bank",
                    "amount": parse_float(grant_amt),
                    "currency": currency,
                    "assistance_type": "grant",
                    "financing_instrument": "IDA Grant",
                    "budget_type": "on_budget",
                    "terms": None,
                    "transaction_date": transaction_date,
                    "transaction_type": "commitment",
                    "is_actual": True,
                    "source": "WB",
                }
            )
        # If neither loan nor grant but totalamt is present
        if not financing_commitments and total_amt and parse_float(total_amt):
            financing_commitments.append(
                {
                    "donor": "World Bank",
                    "amount": parse_float(total_amt),
                    "currency": currency,
                    "assistance_type": "other",
                    "financing_instrument": "Investment Project Financing",
                    "budget_type": "on_budget",
                    "terms": None,
                    "transaction_date": transaction_date,
                    "transaction_type": "commitment",
                    "is_actual": True,
                    "source": "WB",
                }
            )

        # Calculate totals
        total_commitment = parse_float(total_amt) if total_amt else None
        total_disbursement = (
            None  # WB API doesn't typically provide this in project list
        )

        # --- Dates ---
        def parse_iso_date(val):
            if not val:
                return None
            try:
                # Accept YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY, DD/MM/YYYY, YYYY
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y"):
                    try:
                        d = datetime.strptime(str(val), fmt).date()
                        return d.isoformat()
                    except Exception:
                        continue
                return None
            except Exception:
                return None

        date_events = []
        # Approval
        approval_date = (
            raw_project.get("board_approval_date")
            or raw_project.get("boardapprovaldate")
            or raw_project.get("approval_date")
        )
        approval_iso = parse_iso_date(approval_date)
        if approval_iso:
            date_events.append(
                {
                    "date": approval_iso,
                    "type": "APPROVAL",
                    "source": "WB",
                }
            )
        # Start
        start_date = raw_project.get("actual_start_date") or raw_project.get(
            "start_date"
        )
        start_iso = parse_iso_date(start_date)
        if start_iso:
            date_events.append(
                {
                    "date": start_iso,
                    "type": "START",
                    "source": "WB",
                }
            )
        # Closing/completion
        closing_date = (
            raw_project.get("project_completion_date")
            or raw_project.get("closingdate")
            or raw_project.get("end_date")
        )
        closing_iso = parse_iso_date(closing_date)
        if closing_iso:
            date_events.append(
                {
                    "date": closing_iso,
                    "type": "CLOSING",
                    "source": "WB",
                }
            )
        # --- Sector/classification ---
        # NOTE: Locations are handled via LOCATED_IN relationships during migration
        sectors = []
        # Try to use major_sectors, sector1, sector, etc.
        if isinstance(raw_project.get("major_sectors"), list):
            for entry in raw_project["major_sectors"]:
                if isinstance(entry, dict) and "major_sector" in entry:
                    major_sector = entry["major_sector"]
                    if isinstance(major_sector, dict):
                        sector_name = major_sector.get("major_sector_name", "")
                        if sector_name:
                            sectors.append(
                                {
                                    "normalized_sector": None,
                                    "donor_sector": sector_name,
                                    "donor_subsector": None,
                                    "donor": "World Bank",
                                    "percentage": None,
                                }
                            )
                elif isinstance(entry, str):
                    sectors.append(
                        {
                            "normalized_sector": None,
                            "donor_sector": entry,
                            "donor_subsector": None,
                            "donor": "World Bank",
                            "percentage": None,
                        }
                    )
        elif raw_project.get("mjsector"):
            # mjsector is a comma-separated string of sectors
            for sector in str(raw_project.get("mjsector", "")).split(","):
                sector = sector.strip()
                if sector:
                    sectors.append(
                        {
                            "normalized_sector": None,
                            "donor_sector": sector,
                            "donor_subsector": None,
                            "donor": "World Bank",
                            "percentage": None,
                        }
                    )
        elif raw_project.get("sector1"):
            sectors.append(
                {
                    "normalized_sector": None,
                    "donor_sector": raw_project.get("sector1"),
                    "donor_subsector": None,
                    "donor": "World Bank",
                    "percentage": None,
                }
            )
        elif raw_project.get("sector"):
            sectors.append(
                {
                    "normalized_sector": None,
                    "donor_sector": raw_project.get("sector"),
                    "donor_subsector": None,
                    "donor": "World Bank",
                    "percentage": None,
                }
            )
        # --- Tags (themes, climate, etc.) ---
        tags = []
        # Themes
        for t in raw_project.get("themev2_level1_exact") or []:
            tags.append(
                {
                    "category": "THEME",
                    "normalized_tag": None,
                    "donor_tag": t,
                    "donor": "World Bank",
                }
            )
        # Climate
        if raw_project.get("climate_related"):
            tags.append(
                {
                    "category": "CLIMATE",
                    "normalized_tag": None,
                    "donor_tag": str(raw_project.get("climate_related")),
                    "donor": "World Bank",
                }
            )
        # --- Donors and donor_extensions ---
        # NOTE: donors field removed in new schema - donor info is in financing[].donor
        donor_extensions = [
            {
                "donor": "WB",
                "donor_project_id": donor_project_id,
                "raw_payload": raw_project,
            }
        ]
        # --- Project URL ---
        project_url = (
            raw_project.get("url")
            or raw_project.get("project_url")
            or (
                f"https://projects.worldbank.org/en/projects-operations/project-detail/{donor_project_id}"
                if donor_project_id
                else None
            )
        )

        # --- Build slug ---
        slug = f"wb-{donor_project_id}" if donor_project_id else None

        # --- Build names (required by Entity) ---
        names = []
        if title:
            names.append(
                {
                    "kind": "PRIMARY",
                    "en": {"full": title},
                }
            )

        # --- Build description as LangText ---
        description_obj = None
        if description:
            description_obj = {"en": {"value": description, "provenance": "imported"}}

        # --- Compose final dict (new schema) ---
        project_dict = {
            "slug": slug,
            "type": "project",
            "sub_type": "development_project",
            "names": names,
            "description": description_obj,
            "stage": stage,
            "implementing_agency": implementing_agency,
            "executing_agency": executing_agency,
            "financing": financing_commitments if financing_commitments else None,
            "total_commitment": total_commitment,
            "total_disbursement": total_disbursement,
            "dates": date_events if date_events else None,
            "sectors": sectors if sectors else None,
            "tags": tags if tags else None,
            "donor_extensions": donor_extensions,
            "project_url": project_url,
            # Migration metadata for relationship creation
            "_migration_metadata": {
                "wb_project_id": donor_project_id,
                "implementing_agencies": (
                    [{"name": implementing_agency}] if implementing_agency else []
                ),
                "executing_agencies": (
                    [{"name": executing_agency}] if executing_agency else []
                ),
                "development_agencies": [
                    {
                        "name": "World Bank",
                        "architecture": "Multilateral",
                        "group": "MDB",
                    }
                ],
            },
        }
        return project_dict

    def save_to_file(self, data: List[Dict[str, Any]], filename: str = None):
        """Save scraped data to a JSON file.

        Args:
            data: List of project data to save
            filename: Optional filename. If None, generates a filename with timestamp
        """
        # Create world_bank directory if it doesn't exist (for preprocessed data)
        output_dir = os.path.join(os.path.dirname(__file__), "world_bank")
        os.makedirs(output_dir, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"world_bank_nepal_projects_{timestamp}.json"

        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(data)} projects to {filepath}")
        return filepath

    def save_to_migration_file(self, data: List[Dict[str, Any]]):
        """Save scraped data to the file expected by the migration (JSONL format).

        Args:
            data: List of project data to save
        """
        # Save to the location expected by the migration script, in the main source/ directory
        # This is for the final processed data that the migration will use
        project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        output_dir = os.path.join(
            project_root, "migrations", "007-source-projects", "source"
        )
        os.makedirs(output_dir, exist_ok=True)

        migration_file_path = os.path.join(
            output_dir,  # main source directory
            "world_bank_projects.jsonl",  # JSONL format like DFMIS
        )

        # Save as JSONL (one JSON object per line)
        with open(migration_file_path, "w", encoding="utf-8") as f:
            for project in data:
                f.write(json.dumps(project, ensure_ascii=False) + "\n")

        logger.info(
            f"Saved {len(data)} projects to migration file: {migration_file_path}"
        )
        return migration_file_path

    def _parse_date(self, date_str: str) -> str:
        """Parse date string to ISO format.

        Args:
            date_str: Date string in various formats

        Returns:
            Date in ISO format (YYYY-MM-DD) or empty string
        """
        if not date_str:
            return ""

        # Handle various date formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y"):
            try:
                parsed_date = datetime.strptime(str(date_str), fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return str(date_str)  # Return as is if parsing fails

    def _extract_milestones(self, raw_project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract project milestones from raw data.

        Args:
            raw_project: Raw project data

        Returns:
            List of milestone dictionaries
        """
        milestones = []

        # Extract key dates as milestones
        key_dates = [
            ("Board Approval", raw_project.get("board_approval_date")),
            (
                "Start Date",
                raw_project.get("actual_start_date", raw_project.get("start_date")),
            ),
            (
                "Closing Date",
                raw_project.get(
                    "project_completion_date", raw_project.get("closingdate")
                ),
            ),
            ("Last Repayment", raw_project.get("last_repayment_date")),
        ]

        for name, date in key_dates:
            if date:
                milestones.append(
                    {
                        "name": name,
                        "date": self._parse_date(date),
                        "status": (
                            "Completed"
                            if datetime.now()
                            >= datetime.strptime(
                                self._parse_date(date)[:10], "%Y-%m-%d"
                            )
                            else "Planned"
                        ),
                        "description": f"{name} of the project",
                    }
                )

        return milestones

    def _extract_yearly_budget(
        self, raw_project: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract yearly budget breakdown if available.

        Args:
            raw_project: Raw project data

        Returns:
            List of yearly budget dictionaries
        """
        # World Bank data doesn't typically have yearly breakdowns in the standard fields
        # This would require more detailed project documents
        budget_breakdown = []

        # If we have loan/grant amounts, we can create a basic entry
        loan_amount = raw_project.get("loan_amount", raw_project.get("ibrdamt", ""))
        grant_amount = raw_project.get("grant_amount", raw_project.get("grantamt", ""))

        if loan_amount or grant_amount:
            budget_breakdown.append(
                {
                    "year": "Total",
                    "allocated_budget": str(loan_amount),
                    "spent_budget": raw_project.get("totalcommamt", ""),
                    "percentage_spent": self._calculate_percentage_spent(raw_project),
                }
            )

        return budget_breakdown

    def _calculate_cost_overruns(self, raw_project: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential cost overruns.

        Args:
            raw_project: Raw project data

        Returns:
            Cost overrun information dictionary
        """
        total_allocated = raw_project.get(
            "total_amount", raw_project.get("totalamt", "")
        )
        total_disbursed = raw_project.get(
            "total_disbursed", raw_project.get("totalcommamt", "")
        )

        if total_allocated and total_disbursed:
            try:
                allocated = float(str(total_allocated).replace(",", ""))
                disbursed = float(str(total_disbursed).replace(",", ""))

                variance = disbursed - allocated
                percentage = (variance / allocated) * 100 if allocated > 0 else 0

                return {
                    "current_cost": str(total_disbursed),
                    "allocated_budget": str(total_allocated),
                    "variance": str(variance),
                    "percentage": f"{percentage:.2f}%",
                    "is_overrun": variance > 0,
                }
            except (ValueError, TypeError):
                pass

        return {
            "current_cost": str(total_disbursed),
            "allocated_budget": str(total_allocated),
            "variance": "",
            "percentage": "",
            "is_overrun": None,
        }

    def _calculate_financial_progress(self, raw_project: Dict[str, Any]) -> str:
        """Calculate financial progress percentage.

        Args:
            raw_project: Raw project data

        Returns:
            Financial progress as percentage string
        """
        return self._calculate_percentage_spent(raw_project)

    def _calculate_percentage_spent(self, raw_project: Dict[str, Any]) -> str:
        """Calculate percentage of budget spent.

        Args:
            raw_project: Raw project data

        Returns:
            Percentage spent as string
        """
        total_amount = raw_project.get("total_amount", raw_project.get("totalamt", ""))
        total_disbursed = raw_project.get(
            "total_disbursed", raw_project.get("totalcommamt", "")
        )

        if total_amount and total_disbursed:
            try:
                amount = float(str(total_amount).replace(",", ""))
                disbursed = float(str(total_disbursed).replace(",", ""))

                if amount > 0:
                    percentage = (disbursed / amount) * 100
                    return f"{percentage:.2f}%"
            except (ValueError, TypeError):
                pass

        return ""

    def _extract_reports(self, raw_project: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract available reports from project data.

        Args:
            raw_project: Raw project data

        Returns:
            List of report dictionaries
        """
        reports = []

        # Extract project documents as reports if available
        if "project_doc_url" in raw_project:
            reports.append(
                {
                    "type": "Project Document",
                    "url": raw_project["project_doc_url"],
                    "title": "Project Appraisal Document",
                    "date": "",
                }
            )

        if "docs_url" in raw_project:
            reports.append(
                {
                    "type": "Additional Documents",
                    "url": raw_project["docs_url"],
                    "title": "Project Documents",
                    "date": "",
                }
            )

        return reports

    def _extract_budget_amount(self, raw_project: Dict[str, Any]) -> str:
        """Extract total budget amount from raw project data.

        Args:
            raw_project: Raw project data

        Returns:
            Total budget as string
        """
        # Try different possible fields for budget/amount
        amount_fields = [
            "total_amount",
            "totalamt",
            "amount",
            "lending_amount",
            "loan_amount",
            "ibrdamt",
            "ida_amount",
            "grant_amount",
            "grantamt",
            "totalcommamt",
            "curr_project_cost",
        ]

        for field in amount_fields:
            if field in raw_project and raw_project[field]:
                value = raw_project[field]
                # Add currency if not already specified
                if isinstance(value, (int, float)):
                    return f"{value} USD"
                return str(value)

        return ""

    def _extract_loan_amount(self, raw_project: Dict[str, Any]) -> str:
        """Extract loan amount from raw project data.

        Args:
            raw_project: Raw project data

        Returns:
            Loan amount as string
        """
        loan_fields = ["loan_amount", "ibrdamt", "ibrd_amount", "ibrd_commitment"]

        for field in loan_fields:
            if field in raw_project and raw_project[field]:
                value = raw_project[field]
                if isinstance(value, (int, float)):
                    return f"{value} USD"
                return str(value)

        return ""

    def _extract_grant_amount(self, raw_project: Dict[str, Any]) -> str:
        """Extract grant amount from raw project data.

        Args:
            raw_project: Raw project data

        Returns:
            Grant amount as string
        """
        grant_fields = ["grant_amount", "grantamt", "grant_amount_text"]

        for field in grant_fields:
            if field in raw_project and raw_project[field]:
                value = raw_project[field]
                if isinstance(value, (int, float)):
                    return f"{value} USD"
                return str(value)

        return ""

    def _extract_funding_source(self, raw_project: Dict[str, Any]) -> str:
        """Extract funding source from raw project data.

        Args:
            raw_project: Raw project data

        Returns:
            Funding source as string
        """
        # Check for various funding source indicators
        if "lending_instrument" in raw_project:
            instrument = raw_project["lending_instrument"]
            if "loan" in instrument.lower():
                return "World Bank Loan"
            elif "grant" in instrument.lower():
                return "World Bank Grant"

        # Check for specific loan/grant flags
        if raw_project.get("ibrdamt") and float(raw_project.get("ibrdamt", 0)) > 0:
            return "World Bank IBRD Loan"
        if (
            raw_project.get("ida_amount")
            and float(raw_project.get("ida_amount", 0)) > 0
        ):
            return "World Bank IDA Grant"

        # Default
        return "World Bank"

    def _extract_verification_documents(self, raw_project: Dict[str, Any]) -> List[str]:
        """Extract verification documents from raw project data.

        Args:
            raw_project: Raw project data

        Returns:
            List of verification document URLs
        """
        verification_docs = []

        # Check for various document URLs
        doc_fields = [
            "docs_url",
            "regionhomepageurl",
            "countryhomepageurl",
            "project_document_url",
            "url",
            "project_url",
        ]

        for field in doc_fields:
            if field in raw_project and raw_project[field]:
                doc_url = raw_project[field]
                if doc_url not in verification_docs:
                    verification_docs.append(doc_url)

        return verification_docs


# Function to run the scraper independently if needed
async def scrape_world_bank_projects(save_to_file: bool = True) -> List[Dict[str, Any]]:
    """Convenience function to scrape World Bank projects for Nepal."""
    scraper = WorldBankProjectScraper()
    projects = await scraper.search_nepal_projects()

    # Normalize the projects
    normalized_projects = [scraper.normalize_project_data(p) for p in projects]

    # Save to file if requested
    if save_to_file and normalized_projects:
        scraper.save_to_file(normalized_projects)
        scraper.save_to_migration_file(normalized_projects)  # Also save for migration

    return normalized_projects


async def scrape_and_save_world_bank_data():
    """Scrape World Bank data and save to files for migration."""
    logger.info("Starting World Bank data scraping for Nepal...")

    # Create the scraper
    scraper = WorldBankProjectScraper()

    # Scrape projects
    raw_projects = await scraper.search_nepal_projects()
    logger.info(f"Retrieved {len(raw_projects)} raw projects from World Bank APIs")

    # Normalize projects
    normalized_projects = [scraper.normalize_project_data(p) for p in raw_projects]

    # Save raw data
    if raw_projects:
        raw_filepath = scraper.save_to_file(
            raw_projects,
            f"world_bank_nepal_projects_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        logger.info(f"Saved raw data to {raw_filepath}")

    # Save normalized data
    if normalized_projects:
        normalized_filepath = scraper.save_to_file(
            normalized_projects,
            f"world_bank_nepal_projects_normalized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        logger.info(f"Saved normalized data to {normalized_filepath}")

    # Save to migration file
    if normalized_projects:
        migration_filepath = scraper.save_to_migration_file(normalized_projects)
        logger.info(f"Saved data for migration to {migration_filepath}")

    logger.info(f"Scraping completed. {len(normalized_projects)} projects processed.")
    return normalized_projects


if __name__ == "__main__":
    # Example usage
    async def main():
        projects = await scrape_and_save_world_bank_data()
        print(f"Scraped and saved {len(projects)} projects from World Bank")
        if projects:
            print("Sample project:")
            print(json.dumps(projects[0], indent=2))

    # Run the example
    asyncio.run(main())
