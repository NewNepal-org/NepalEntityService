"""Scraping Service for nes.

The Scraping Service is a standalone service for extracting and normalizing data
from external sources using GenAI/LLM capabilities. It does not directly access
the database but returns normalized data for client applications to process.

Core Components:
- Web Scraper: Multi-source data extraction (Wikipedia, government sites, news)
- Translation Service: Nepali/English translation and transliteration
- Data Normalization Service: LLM-powered data structuring
"""

from .normalization import (
    AttributeExtractor,
    DataNormalizer,
    DataQualityAssessor,
    NameExtractor,
    RelationshipExtractor,
)
from .service import ScrapingService
from .web_scraper import RateLimiter, RetryHandler, WebScraper
from .wikipedia_scraper import WikipediaScraper

__all__ = [
    "ScrapingService",
    "WebScraper",
    "WikipediaScraper",
    "RateLimiter",
    "RetryHandler",
    "DataNormalizer",
    "NameExtractor",
    "AttributeExtractor",
    "RelationshipExtractor",
    "DataQualityAssessor",
]
