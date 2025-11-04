"""Wikipedia Nepali politicians scraper."""

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

from datetime import datetime

import wikipedia
from bs4 import BeautifulSoup

from nes.core.identifiers.builders import build_entity_id
from nes.core.models import Person
from nes.core.models.entity import Entity
from nes.core.models.version import Actor, Version
from nes.scraping.llm.google_cloud import GoogleCloudEntityScraper

skip_tags = {"sup", "cite"}


def get_entity_schema() -> dict:
    """Get the schema for the Person entity."""
    schema = Person.model_json_schema()

    del schema["$defs"]["Actor"]
    del schema["$defs"]["Version"]
    del schema["properties"]["type"]
    del schema["properties"]["subType"]
    del schema["properties"]["versionSummary"]
    del schema["properties"]["createdAt"]

    return schema


def is_bad_anchor(element):
    """Check if the given element is a reference anchor."""
    for elem in (
        element,
        element.parent,
        element.parent.parent,
        element.parent.parent.parent,
    ):
        if elem.name in skip_tags:
            return True
        if "reference-text" in elem.get("class", []):
            return True

    if any(
        x.name in skip_tags for x in (element, element.parent, element.parent.parent)
    ):
        return True

    if element["href"].startswith("#"):
        return True
    if "action=edit" in element["href"]:
        return True

    return False


def clean_content(content):
    """Convert wiki notation headers to markdown."""
    import re

    # Convert wiki headers (== Header ==) to markdown (## Header)
    content = re.sub(r"={6}\s*(.+?)\s*={6}", r"###### \1", content)
    content = re.sub(r"={5}\s*(.+?)\s*={5}", r"##### \1", content)
    content = re.sub(r"={4}\s*(.+?)\s*={4}", r"#### \1", content)
    content = re.sub(r"={3}\s*(.+?)\s*={3}", r"### \1", content)
    content = re.sub(r"={2}\s*(.+?)\s*={2}", r"## \1", content)

    return content


def unstructured_to_entity(content, metadata):
    message = f"""
I am extracting people information from Wikipedia into a structured JSON database with high quality and accuracy rather than completeness.
Extract the person from the following text and return them in JSON.

The person schema: {get_entity_schema()}

Metadata: {metadata}

The person bio: {content}
"""

    scraper = GoogleCloudEntityScraper()

    result = scraper.extract_single_entity(message, "person")
    person_slug = result["slug"]
    entity_type = "person"
    entity_subtype = None
    created_at = datetime.now()
    entity_id = build_entity_id(
        type=entity_type, subtype=entity_subtype, slug=person_slug
    )

    version = Version(
        entityOrRelationshipId=entity_id,
        type="ENTITY",
        versionNumber=1,
        actor=Actor(slug="system", name="System user"),
        changeDescription="Initial version",
        createdAt=created_at,
        changes=result,
    )

    result["versionSummary"] = version
    result["type"] = entity_type
    result["subtype"] = entity_subtype
    result["createdAt"] = created_at

    entity = Entity(**result)

    if entity.identifiers is None:
        entity.identifiers = {}

    entity.identifiers["wikipedia"] = metadata["Wikipedia links"]

    return entity


async def traverse_politician_page(name, href):
    """Traverse a politician page by processing the href and making a Wikipedia lookup."""
    # Remove /wiki/ prefix and replace _ with spaces
    page_title = href.replace("/wiki/", "")

    contents = []
    urls = []

    # Extract content from both English and Nepali
    for lang in ["en", "ne"]:
        try:
            wikipedia.set_lang(lang)
            page = wikipedia.page(page_title)
            content = BeautifulSoup(page.html(), "html.parser").text
            contents.append(f"=== {lang.upper()} Content ===\n{content}")
            urls.append(page.url)
        except wikipedia.exceptions.DisambiguationError as e:
            # Try the first option if disambiguation
            try:
                page = wikipedia.page(e.options[0])
                content = BeautifulSoup(page.html(), "html.parser").text
                contents.append(f"=== {lang.upper()} Content ===\n{content}")
                urls.append(page.url)
            except:
                raise
        except wikipedia.exceptions.PageError:
            # Page not found
            continue

    if not contents:
        return None

    combined_content = "\n\n".join(contents)
    entity = unstructured_to_entity(
        combined_content, {"Politician name": name, "Wikipedia links": urls}
    )
    return entity


def get_nepali_politician_page_links():
    """Get all politician links from Wikipedia page after section A until References."""
    page = wikipedia.page("List of Nepalese politicians")
    html = page.html()
    soup = BeautifulSoup(html, "html.parser")

    # Find element with id="A"
    a_element = soup.find(id="A")
    if not a_element:
        return []

    # Find References element to stop at
    references_element = soup.find(id="References")

    # Get all <a> tags after the element with id="A" until References
    links = []
    for element in a_element.find_all_next("a", href=True):
        # Stop if we reach the References section
        if (
            references_element
            and element.find_parent()
            and references_element in element.find_parents()
        ):
            break

        if is_bad_anchor(element):
            continue

        links.append({"name": element["title"], "href": element["href"]})

    return links


if __name__ == "__main__":
    import asyncio

    from nes.database import get_database

    async def main():
        db = get_database()
        links = get_nepali_politician_page_links()
        print(f"Found {len(links)} politician links")

        for i, link in enumerate(links):
            if i < 25:
                continue
            print(f"Processing {i}/{len(links)}: {link['name']}")
            try:
                entity = await traverse_politician_page(link["name"], link["href"])
                if entity:
                    await db.put_entity(entity)
                    print(f"Successfully saved: {entity.id}")
                else:
                    print(f"Failed to load: {link['name']}")
            except Exception as e:
                print(f"Error processing {link['name']}: {e}")
            # break

    asyncio.run(main())
