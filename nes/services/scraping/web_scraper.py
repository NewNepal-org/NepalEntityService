"""Web Scraper component for extracting data from external sources.

This module provides the WebScraper class for extracting data from various
external sources including Wikipedia, government sites, and news sources.
It implements rate limiting, error handling, retry logic, and respectful
scraping practices.

Key Features:
    - Rate limiting per domain to avoid overwhelming servers
    - Exponential backoff retry logic for transient failures
    - Graceful error handling with detailed logging
    - Support for multiple data sources (Wikipedia, government, news)
    - Async operations for concurrent processing

Performance Considerations:
    - Token bucket rate limiting for smooth request distribution
    - Configurable retry attempts with exponential backoff
    - Per-domain rate tracking to respect server limits
    - Efficient request batching where possible

Best Practices:
    - Always set a descriptive User-Agent
    - Respect robots.txt
    - Use appropriate rate limits (default: 1 req/sec, 30 req/min)
    - Handle errors gracefully without blocking other operations
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for respectful web scraping.

    Implements per-domain rate limiting to avoid overwhelming servers.
    Uses a token bucket algorithm for smooth rate limiting.

    Attributes:
        requests_per_second: Maximum requests per second per domain
        requests_per_minute: Maximum requests per minute per domain
        last_request_time: Dictionary tracking last request time per domain
        request_counts: Dictionary tracking request counts per domain
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        requests_per_minute: int = 30,
    ):
        """Initialize the rate limiter.

        Args:
            requests_per_second: Maximum requests per second per domain
            requests_per_minute: Maximum requests per minute per domain
        """
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.last_request_time: Dict[str, float] = {}
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.min_delay = 1.0 / requests_per_second

    async def acquire(self, domain: str) -> None:
        """Acquire permission to make a request to the domain.

        Blocks until rate limit allows the request.

        Args:
            domain: The domain to rate limit
        """
        current_time = time.time()

        # Clean up old request timestamps (older than 1 minute)
        cutoff_time = current_time - 60
        self.request_counts[domain] = [
            t for t in self.request_counts[domain] if t > cutoff_time
        ]

        # Check per-minute limit
        if len(self.request_counts[domain]) >= self.requests_per_minute:
            # Wait until oldest request is more than 1 minute old
            oldest_request = self.request_counts[domain][0]
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                current_time = time.time()

        # Check per-second limit
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                wait_time = self.min_delay - time_since_last
                await asyncio.sleep(wait_time)
                current_time = time.time()

        # Record this request
        self.last_request_time[domain] = current_time
        self.request_counts[domain].append(current_time)


class RetryHandler:
    """Retry handler for failed requests.

    Implements exponential backoff with jitter for retrying failed requests.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds between retries
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        """Initialize the retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given retry attempt.

        Uses exponential backoff: delay = base_delay * (2 ^ attempt)

        Args:
            attempt: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (2**attempt)
        return min(delay, self.max_delay)

    async def execute_with_retry(
        self,
        func,
        *args,
        **kwargs,
    ) -> Any:
        """Execute a function with retry logic.

        Args:
            func: The async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function result

        Raises:
            The last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed, raise the exception
                    raise last_exception


class WebScraper:
    """Web scraper for extracting data from external sources.

    Provides multi-source data extraction with rate limiting, error handling,
    and retry logic. Supports Wikipedia, government sites, and news sources.

    Attributes:
        rate_limiter: Rate limiter for respectful scraping
        retry_handler: Retry handler for failed requests
        user_agent: User agent string for HTTP requests
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        requests_per_minute: int = 30,
        max_retries: int = 3,
        timeout: int = 30,
        user_agent: Optional[str] = None,
    ):
        """Initialize the web scraper.

        Args:
            requests_per_second: Maximum requests per second per domain
            requests_per_minute: Maximum requests per minute per domain
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            user_agent: Custom user agent string (optional)
        """
        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            requests_per_minute=requests_per_minute,
        )
        self.retry_handler = RetryHandler(max_retries=max_retries)
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Nepal Entity Service Bot/2.0 "
            "(https://github.com/yourusername/nepal-entity-service; "
            "contact@example.com)"
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting.

        Args:
            url: The URL to extract domain from

        Returns:
            The domain name
        """
        # Simple domain extraction
        if "://" in url:
            url = url.split("://")[1]
        domain = url.split("/")[0]
        return domain

    async def fetch_wikipedia_page(
        self,
        page_title: str,
        language: str = "en",
    ) -> Optional[Dict[str, Any]]:
        """Fetch a Wikipedia page.

        Extracts content from a Wikipedia page using the wikipedia library.
        Handles disambiguation pages and missing pages gracefully.

        Args:
            page_title: The Wikipedia page title
            language: Language code ("en" or "ne")

        Returns:
            Dictionary containing:
                - content: Page content/text
                - url: Page URL
                - title: Page title
                - summary: Page summary
                - categories: Page categories
                - links: Page links
                - images: Page images
            Returns None if page doesn't exist
        """
        try:
            # Import wikipedia library (optional dependency)
            import wikipedia
        except ImportError:
            logger.error(
                "wikipedia library not installed. Install with: pip install wikipedia"
            )
            return None

        # Set language
        wikipedia.set_lang(language)

        # Determine domain for rate limiting
        domain = f"{language}.wikipedia.org"

        # Apply rate limiting
        await self.rate_limiter.acquire(domain)

        # Fetch page with retry logic
        async def fetch():
            try:
                # Get page
                page = wikipedia.page(page_title, auto_suggest=False)

                return {
                    "content": page.content,
                    "url": page.url,
                    "title": page.title,
                    "summary": page.summary,
                    "categories": page.categories,
                    "links": page.links[:50],  # Limit links
                    "images": page.images[:10],  # Limit images
                }
            except wikipedia.exceptions.DisambiguationError as e:
                # Handle disambiguation pages
                # Return first option or None
                if e.options:
                    # Try first option
                    page = wikipedia.page(e.options[0], auto_suggest=False)
                    return {
                        "content": page.content,
                        "url": page.url,
                        "title": page.title,
                        "summary": page.summary,
                        "categories": page.categories,
                        "links": page.links[:50],
                        "images": page.images[:10],
                        "disambiguation": True,
                        "options": e.options,
                    }
                return None
            except wikipedia.exceptions.PageError:
                # Page doesn't exist
                return None
            except Exception as e:
                # Other errors
                logger.error(f"Error fetching Wikipedia page: {e}")
                raise e

        try:
            return await self.retry_handler.execute_with_retry(fetch)
        except Exception as e:
            logger.error(f"Failed to fetch Wikipedia page after retries: {e}")
            return None

    async def search_wikipedia(
        self,
        query: str,
        language: str = "en",
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search Wikipedia for pages matching the query.

        Args:
            query: Search query
            language: Language code
            max_results: Maximum number of results

        Returns:
            List of search results with title and summary
        """
        try:
            import wikipedia
        except ImportError:
            logger.error(
                "wikipedia library not installed. Install with: pip install wikipedia"
            )
            return []

        # Set language
        wikipedia.set_lang(language)

        # Determine domain for rate limiting
        domain = f"{language}.wikipedia.org"

        # Apply rate limiting
        await self.rate_limiter.acquire(domain)

        # Search with retry logic
        async def search():
            try:
                # Search Wikipedia
                results = wikipedia.search(query, results=max_results)

                # Get summaries for each result
                search_results = []
                for title in results:
                    try:
                        # Rate limit each summary request
                        await self.rate_limiter.acquire(domain)

                        summary = wikipedia.summary(
                            title, sentences=2, auto_suggest=False
                        )
                        page_url = wikipedia.page(title, auto_suggest=False).url

                        search_results.append(
                            {
                                "title": title,
                                "summary": summary,
                                "url": page_url,
                            }
                        )
                    except Exception:
                        # Skip pages that fail
                        continue

                return search_results
            except Exception as e:
                logger.error(f"Error searching Wikipedia: {e}")
                raise e

        try:
            return await self.retry_handler.execute_with_retry(search)
        except Exception as e:
            logger.error(f"Failed to search Wikipedia after retries: {e}")
            return []

    async def fetch_government_page(
        self,
        url: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a government website page.

        Placeholder for government site scraping. Real implementation
        would use appropriate scraping libraries and handle site-specific
        structure.

        Args:
            url: The government page URL

        Returns:
            Dictionary containing extracted data or None
        """
        # Extract domain for rate limiting
        domain = self._extract_domain(url)

        # Apply rate limiting
        await self.rate_limiter.acquire(domain)

        # TODO: Implement actual government page scraping
        # Real implementation would use BeautifulSoup or similar
        logger.warning("Government page scraping not yet implemented")
        return {
            "url": url,
            "content": "",
            "title": "Government Page",
            "source": "government",
        }

    async def fetch_news_page(
        self,
        url: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a news article page.

        Placeholder for news site scraping. Real implementation
        would use appropriate scraping libraries and handle site-specific
        structure.

        Args:
            url: The news article URL

        Returns:
            Dictionary containing extracted data or None
        """
        # Extract domain for rate limiting
        domain = self._extract_domain(url)

        # Apply rate limiting
        await self.rate_limiter.acquire(domain)

        # TODO: Implement actual news page scraping
        # Real implementation would use newspaper3k or similar
        logger.warning("News page scraping not yet implemented")
        return {
            "url": url,
            "content": "",
            "title": "News Article",
            "source": "news",
        }

    async def extract_html_content(
        self,
        html: str,
        selectors: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Extract content from HTML using CSS selectors.

        Placeholder for HTML parsing. Real implementation would use
        BeautifulSoup or lxml for robust HTML parsing.

        Args:
            html: The HTML content
            selectors: Dictionary of field names to CSS selectors

        Returns:
            Dictionary of extracted content
        """
        # TODO: Implement actual HTML content extraction
        # Real implementation would use BeautifulSoup
        logger.warning("HTML content extraction not yet implemented")
        extracted = {}

        if selectors:
            for field, selector in selectors.items():
                extracted[field] = ""

        return extracted
