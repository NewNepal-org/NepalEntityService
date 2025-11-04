"""Google Cloud LLM entity scraper implementation."""

import json
import os
from typing import List, Optional

import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel

from nes.core.models import Entity, Organization, Person
from nes.core.models.entity import ENTITY_TYPES

from .base import LLMEntityScraper


class GoogleCloudEntityScraper(LLMEntityScraper):
    """Google Cloud Vertex AI implementation of LLM entity scraper."""

    def __init__(
        self,
        service_account_key_path: str = ".service-account-key.json",
        location: str = "us-central1",
        model_name: str = "gemini-2.5-pro",
    ):
        """Initialize Google Cloud entity scraper.

        Args:
            service_account_key_path: Path to service account JSON key file
            location: Google Cloud region
            model_name: Vertex AI model name
        """
        if not os.path.exists(service_account_key_path):
            raise FileNotFoundError(
                f"Service account key file not found: {service_account_key_path}"
            )

        credentials = service_account.Credentials.from_service_account_file(
            service_account_key_path
        )
        vertexai.init(
            project=credentials.project_id, location=location, credentials=credentials
        )
        self.model = GenerativeModel(model_name)

    def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        overrides: Optional[dict] = None,
    ) -> List[Entity]:
        """Extract entities from text using Vertex AI."""
        entity_types = entity_types or ENTITY_TYPES

        prompt = f"""Extract entities from the following text and return them as JSON.
        
Entity types to extract: {', '.join(entity_types)}

Text:
{text}

Return only valid json JSON array of entities without backticks markdown."""

        response = self.model.generate_content(prompt)

        try:
            text = response.text
            if text.startswith("```json"):
                text = text[7:-3]

            entities_data = json.loads(text)

            return entities_data
            entities = []

            for data in entities_data:
                # Apply overrides if provided
                if overrides:
                    data.update(overrides)

                entity_type = data.get("type", "").lower()
                if entity_type == "person":
                    entity = Person(**data)
                elif entity_type == "organization":
                    entity = Organization(**data)
                else:
                    entity = Entity(**data)
                entities.append(entity)

            return entities
        except (json.JSONDecodeError, KeyError):
            return []

    def extract_single_entity(self, text: str, entity_type: str) -> Optional[Entity]:
        """Extract single entity from text."""
        entities = self.extract_entities(text, [entity_type])
        return entities[0] if entities else None
