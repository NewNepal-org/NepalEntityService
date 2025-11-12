# Scraping Service Guide

This guide covers the Scraping Service, which provides data extraction and normalization capabilities for building entity databases from external sources.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Service API](#service-api)
4. [CLI Commands](#cli-commands)
5. [Common Use Cases](#common-use-cases)
6. [LLM Providers](#llm-providers)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Scraping Service provides:

- **Wikipedia Data Extraction**: Extract entity data from English and Nepali Wikipedia
- **Data Normalization**: Convert unstructured text to structured entity data using LLM
- **Relationship Extraction**: Identify relationships from narrative text
- **Translation**: Translate between Nepali and English with transliteration
- **External Search**: Search multiple sources for entity information

### Key Features

- **LLM-Powered**: Uses AI models for intelligent data extraction
- **Multilingual**: Supports both Nepali (Devanagari) and English
- **Pluggable Architecture**: Supports multiple LLM providers (Mock, AWS Bedrock, etc.)
- **Rate Limiting**: Built-in rate limiting to respect external sources
- **Error Handling**: Graceful degradation with detailed error logging

---

## Getting Started

### Installation

Install with scraping support:

```bash
pip install nepal-entity-service[scraping]
```

Or install all features:

```bash
pip install nepal-entity-service[all]
```

### Basic Usage

```python
from nes.services.scraping import ScrapingService
from nes.services.scraping.providers import MockLLMProvider

# Initialize with mock provider (for testing)
provider = MockLLMProvider()
service = ScrapingService(llm_provider=provider)

# Extract from Wikipedia
data = await service.extract_from_wikipedia(
    page_title="Ram_Chandra_Poudel",
    language="en"
)

# Normalize to entity structure
normalized = await service.normalize_person_data(
    raw_data=data,
    source="wikipedia"
)

print(f"Created entity: {normalized['slug']}")
```

---

## Service API

### Initialization

```python
from nes.services.scraping import ScrapingService
from nes.services.scraping.providers import MockLLMProvider

# Basic initialization
provider = MockLLMProvider()
service = ScrapingService(llm_provider=provider)

# With custom components (for testing)
from nes.services.scraping.web_scraper import WebScraper
from nes.services.scraping.translation import Translator

custom_scraper = WebScraper(rate_limit=2.0)  # 2 seconds between requests
service = ScrapingService(
    llm_provider=provider,
    web_scraper=custom_scraper
)
```

### Extract from Wikipedia

Extract content from Wikipedia pages:

```python
# Extract from English Wikipedia
data = await service.extract_from_wikipedia(
    page_title="Ram_Chandra_Poudel",
    language="en"
)

# Extract from Nepali Wikipedia
data = await service.extract_from_wikipedia(
    page_title="राम_चन्द्र_पौडेल",
    language="ne"
)

# Handle missing pages
data = await service.extract_from_wikipedia(
    page_title="Nonexistent_Page",
    language="en"
)
if data is None:
    print("Page not found")
```

**Returns**:
```python
{
    "content": "Ram Chandra Poudel is a Nepali politician...",
    "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel",
    "title": "Ram Chandra Poudel",
    "language": "en",
    "metadata": {
        "source": "wikipedia",
        "extractor": "wikipedia",
        "language": "en",
        "page_title": "Ram_Chandra_Poudel"
    }
}
```

### Normalize Person Data

Convert raw text to structured entity data:

```python
# Normalize Wikipedia data
raw_data = {
    "content": "Ram Chandra Poudel is a Nepali politician...",
    "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel",
    "title": "Ram Chandra Poudel"
}

normalized = await service.normalize_person_data(
    raw_data=raw_data,
    source="wikipedia"
)

# Normalize custom text
raw_data = {
    "content": "John Doe is a politician from Kathmandu."
}

normalized = await service.normalize_person_data(
    raw_data=raw_data,
    source="manual"
)
```

**Returns**:
```python
{
    "slug": "ram-chandra-poudel",
    "type": "person",
    "sub_type": "politician",
    "names": [
        {
            "kind": "PRIMARY",
            "en": {"full": "Ram Chandra Poudel"},
            "ne": {"full": "राम चन्द्र पौडेल"}
        }
    ],
    "identifiers": [
        {
            "scheme": "wikipedia",
            "value": "Ram_Chandra_Poudel"
        }
    ],
    "attributes": {
        "occupation": "politician",
        "nationality": "Nepali"
    }
}
```

### Extract Relationships

Identify relationships from narrative text:

```python
text = """
Ram Chandra Poudel is a member of the Nepali Congress party.
He served as Deputy Prime Minister from 2007 to 2009.
"""

relationships = await service.extract_relationships(
    text=text,
    entity_id="entity:person/ram-chandra-poudel"
)

for rel in relationships:
    print(f"{rel['type']}: {rel['target_entity']['name']}")
```

**Returns**:
```python
[
    {
        "type": "MEMBER_OF",
        "target_entity": {
            "name": "Nepali Congress",
            "id": "entity:organization/political_party/nepali-congress"
        },
        "attributes": {}
    },
    {
        "type": "HELD_POSITION",
        "target_entity": {
            "name": "Deputy Prime Minister"
        },
        "start_date": "2007-01-01",
        "end_date": "2009-12-31",
        "attributes": {}
    }
]
```

### Translate Text

Translate between Nepali and English:

```python
# Nepali to English
result = await service.translate(
    text="राम चन्द्र पौडेल",
    source_lang="ne",
    target_lang="en"
)
print(result["translated_text"])  # "Ram Chandra Poudel"

# English to Nepali
result = await service.translate(
    text="Ram Chandra Poudel",
    source_lang="en",
    target_lang="ne"
)
print(result["translated_text"])  # "राम चन्द्र पौडेल"

# Auto-detect source language
result = await service.translate(
    text="राम चन्द्र पौडेल",
    target_lang="en"
)
print(result["detected_language"])  # "ne"
```

**Returns**:
```python
{
    "translated_text": "Ram Chandra Poudel",
    "source_language": "ne",
    "target_language": "en",
    "detected_language": "ne",  # if auto-detected
    "transliteration": "raam chandra poudel"
}
```

### Search External Sources

Search multiple sources for entity information:

```python
# Search Wikipedia only
results = await service.search_external_sources(
    query="Ram Chandra Poudel",
    sources=["wikipedia"]
)

# Search multiple sources
results = await service.search_external_sources(
    query="Ram Chandra Poudel",
    sources=["wikipedia", "government", "news"]
)

for result in results:
    print(f"{result['source']}: {result['title']}")
    print(f"  URL: {result['url']}")
```

**Returns**:
```python
[
    {
        "source": "wikipedia",
        "title": "Ram Chandra Poudel",
        "url": "https://en.wikipedia.org/wiki/Ram_Chandra_Poudel",
        "summary": "Ram Chandra Poudel is a Nepali politician..."
    },
    {
        "source": "government",
        "title": "Ram Chandra Poudel - Government Records",
        "url": "https://example.gov.np/records/...",
        "summary": "Government records for Ram Chandra Poudel"
    }
]
```

---

## CLI Commands

The Scraping Service provides CLI commands for common operations.

### Extract from Wikipedia

```bash
# Extract from English Wikipedia
nes scrape wikipedia "Ram_Chandra_Poudel" --language en

# Extract from Nepali Wikipedia
nes scrape wikipedia "राम_चन्द्र_पौडेल" --language ne

# Save to file
nes scrape wikipedia "Ram_Chandra_Poudel" --output data.json
```

### Normalize Data

```bash
# Normalize from file
nes scrape normalize data.json --source wikipedia --output normalized.json

# Normalize from stdin
cat data.json | nes scrape normalize --source wikipedia
```

### Translate Text

```bash
# Translate Nepali to English
nes translate --to en "राम चन्द्र पौडेल"

# Translate English to Nepali
nes translate --to ne "Ram Chandra Poudel"

# With explicit source language
nes translate --from ne --to en "राम चन्द्र पौडेल"

# Use different AWS region
nes translate --region us-west-2 --to ne "Hello"
```

For detailed CLI usage, see the [Translation Guide](../consumers/translation-guide.md).

### Search External Sources

```bash
# Search Wikipedia
nes scrape search "Ram Chandra Poudel" --sources wikipedia

# Search multiple sources
nes scrape search "Ram Chandra Poudel" --sources wikipedia government news

# Save results
nes scrape search "Ram Chandra Poudel" --sources wikipedia --output results.json
```

---

## Common Use Cases

### Use Case 1: Import Politicians from Wikipedia

```python
async def import_politician_from_wikipedia(page_title: str):
    """Import a politician from Wikipedia."""
    
    # Extract Wikipedia data
    wiki_data = await service.extract_from_wikipedia(
        page_title=page_title,
        language="en"
    )
    
    if not wiki_data:
        print(f"Wikipedia page not found: {page_title}")
        return None
    
    # Normalize to entity structure
    entity_data = await service.normalize_person_data(
        raw_data=wiki_data,
        source="wikipedia"
    )
    
    # Extract relationships
    relationships = await service.extract_relationships(
        text=wiki_data["content"],
        entity_id=f"entity:person/{entity_data['slug']}"
    )
    
    return {
        "entity": entity_data,
        "relationships": relationships
    }

# Use in migration
result = await import_politician_from_wikipedia("Ram_Chandra_Poudel")
if result:
    print(f"Imported: {result['entity']['slug']}")
    print(f"Found {len(result['relationships'])} relationships")
```

### Use Case 2: Batch Import from List

```python
async def batch_import_politicians(page_titles: List[str]):
    """Batch import politicians from Wikipedia."""
    
    results = []
    
    for page_title in page_titles:
        try:
            # Extract and normalize
            wiki_data = await service.extract_from_wikipedia(
                page_title=page_title,
                language="en"
            )
            
            if not wiki_data:
                print(f"Skipping {page_title}: not found")
                continue
            
            entity_data = await service.normalize_person_data(
                raw_data=wiki_data,
                source="wikipedia"
            )
            
            results.append(entity_data)
            print(f"✓ Imported: {entity_data['slug']}")
            
        except Exception as e:
            print(f"✗ Failed {page_title}: {e}")
            continue
    
    return results

# Use in migration
politicians = [
    "Ram_Chandra_Poudel",
    "Sher_Bahadur_Deuba",
    "Pushpa_Kamal_Dahal"
]

results = await batch_import_politicians(politicians)
print(f"Imported {len(results)} politicians")
```

### Use Case 3: Translate Entity Names

```python
async def translate_entity_names(entities: List[Dict]):
    """Translate entity names to Nepali."""
    
    for entity in entities:
        for name in entity["names"]:
            if name["kind"] == "PRIMARY" and "en" in name:
                # Translate English name to Nepali
                result = await service.translate(
                    text=name["en"]["full"],
                    source_lang="en",
                    target_lang="ne"
                )
                
                # Add Nepali name
                name["ne"] = {"full": result["translated_text"]}
                
                print(f"{name['en']['full']} → {name['ne']['full']}")
    
    return entities
```

### Use Case 4: Search and Import

```python
async def search_and_import(query: str):
    """Search for entity and import if found."""
    
    # Search external sources
    results = await service.search_external_sources(
        query=query,
        sources=["wikipedia"]
    )
    
    if not results:
        print(f"No results found for: {query}")
        return None
    
    # Use first result
    first_result = results[0]
    print(f"Found: {first_result['title']}")
    
    # Extract page title from URL
    page_title = first_result["url"].split("/")[-1]
    
    # Import from Wikipedia
    return await import_politician_from_wikipedia(page_title)
```

---

## LLM Providers

The Scraping Service supports multiple LLM providers for data normalization.

### Mock Provider (Testing)

```python
from nes.services.scraping.providers import MockLLMProvider

provider = MockLLMProvider()
service = ScrapingService(llm_provider=provider)
```

**Use for**:
- Testing and development
- CI/CD pipelines
- Demos without API costs

### AWS Bedrock Provider

```python
from nes.services.scraping.providers import AWSBedrockProvider

provider = AWSBedrockProvider(
    region_name="us-east-1",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
)
service = ScrapingService(llm_provider=provider)
```

**Configuration**:
- Requires AWS credentials configured
- Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Or use IAM roles in AWS environment

**Use for**:
- Production data extraction
- High-quality normalization
- Large-scale imports

### Custom Provider

Implement your own provider:

```python
from nes.services.scraping.providers import BaseLLMProvider

class CustomProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "custom"
    
    @property
    def model_id(self) -> str:
        return "custom-model-v1"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        return response_text

provider = CustomProvider()
service = ScrapingService(llm_provider=provider)
```

---

## Best Practices

### 1. Use Mock Provider for Testing

```python
# In tests
provider = MockLLMProvider()
service = ScrapingService(llm_provider=provider)

# In production
provider = AWSBedrockProvider(region_name="us-east-1")
service = ScrapingService(llm_provider=provider)
```

### 2. Handle Missing Pages Gracefully

```python
data = await service.extract_from_wikipedia(
    page_title=page_title,
    language="en"
)

if data is None:
    print(f"Page not found: {page_title}")
    return None

# Continue processing
```

### 3. Validate Normalized Data

```python
normalized = await service.normalize_person_data(
    raw_data=wiki_data,
    source="wikipedia"
)

# Validate required fields
if not normalized.get("slug"):
    print("Warning: No slug generated")

if not normalized.get("names"):
    print("Warning: No names extracted")
```

### 4. Rate Limit External Requests

```python
# Built-in rate limiting
scraper = WebScraper(rate_limit=2.0)  # 2 seconds between requests
service = ScrapingService(
    llm_provider=provider,
    web_scraper=scraper
)

# Or add delays in batch operations
for page_title in page_titles:
    data = await service.extract_from_wikipedia(page_title, "en")
    await asyncio.sleep(1.0)  # Additional delay
```

### 5. Log Progress in Batch Operations

```python
total = len(page_titles)
for i, page_title in enumerate(page_titles, 1):
    print(f"Processing {i}/{total}: {page_title}")
    
    data = await service.extract_from_wikipedia(page_title, "en")
    if data:
        print(f"  ✓ Extracted {len(data['content'])} characters")
    else:
        print(f"  ✗ Not found")
```

### 6. Cache Extracted Data

```python
import json
from pathlib import Path

cache_dir = Path("cache")
cache_dir.mkdir(exist_ok=True)

async def extract_with_cache(page_title: str):
    cache_file = cache_dir / f"{page_title}.json"
    
    # Check cache
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    
    # Extract from Wikipedia
    data = await service.extract_from_wikipedia(page_title, "en")
    
    # Save to cache
    if data:
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)
    
    return data
```

---

## Troubleshooting

### Issue 1: Wikipedia Page Not Found

**Symptom**: `extract_from_wikipedia` returns `None`

**Solutions**:
- Check page title spelling (case-sensitive)
- Use underscores instead of spaces: `Ram_Chandra_Poudel`
- Try searching first: `search_external_sources`
- Check if page exists in the specified language

### Issue 2: Poor Normalization Quality

**Symptom**: Normalized data is incomplete or incorrect

**Solutions**:
- Use AWS Bedrock provider instead of Mock provider
- Provide more context in raw_data
- Check source text quality
- Validate and manually correct results

### Issue 3: Rate Limiting Errors

**Symptom**: HTTP 429 errors or connection failures

**Solutions**:
- Increase rate limit delay: `WebScraper(rate_limit=3.0)`
- Add delays between batch operations
- Reduce concurrent requests
- Use caching to avoid repeated requests

### Issue 4: Translation Errors

**Symptom**: Translation returns unexpected results

**Solutions**:
- Specify source language explicitly
- Check input text encoding (UTF-8)
- Verify target language is "en" or "ne"
- Use transliteration for proper nouns

### Issue 5: AWS Credentials Not Found

**Symptom**: `AWSBedrockProvider` fails to initialize

**Solutions**:
```bash
# Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Or use AWS CLI configuration
aws configure
```

---

## Additional Resources

- [Migration Contributor Guide](migration-contributor-guide.md) - Using scraping in migrations
- [Data Models](data-models.md) - Entity schema reference
- [API Guide](api-guide.md) - REST API documentation

---

**Last Updated:** 2024  
**Version:** 2.0
