"""Data Normalization component for structuring unstructured data.

This module provides LLM-powered data normalization utilities for:
- Extracting structured data from unstructured text
- Relationship discovery from narrative text
- Name disambiguation and standardization
- Data quality assessment

The component uses LLM providers to intelligently extract and structure
entity and relationship data from various text sources.

Architecture:
    - NameExtractor: Identifies and structures person names
    - AttributeExtractor: Extracts entity attributes (position, party, etc.)
    - RelationshipExtractor: Discovers entity relationships from text
    - DataQualityAssessor: Evaluates completeness and quality
    - DataNormalizer: Coordinates all extraction components

Extraction Strategy:
    - Pattern-based extraction for common structures
    - LLM-powered extraction for complex cases (future)
    - Fallback mechanisms for missing data
    - Quality scoring for extracted data

Data Quality:
    - Required field validation
    - Completeness scoring
    - Recommendation generation
    - Issue identification and reporting

Cultural Context:
    - Nepali name structure handling
    - Political party and position recognition
    - Administrative hierarchy understanding
    - Bilingual name extraction (Nepali/English)
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class NameExtractor:
    """Name extractor for identifying and structuring person names.

    Extracts names from text and structures them according to the entity
    name schema, handling both English and Nepali names.

    Attributes:
        name_patterns: Regular expression patterns for name extraction
    """

    def __init__(self):
        """Initialize the name extractor."""
        # Patterns for extracting names from text
        self.name_patterns = [
            # Pattern: "Name (नेपाली नाम)"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([^\)]+)\)",
            # Pattern: "Name" at start of sentence
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            # Pattern: Title + Name
            r"(?:Mr\.|Mrs\.|Dr\.|President|Prime Minister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]

    def extract_names(
        self,
        text: str,
        title: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract names from text.

        Identifies person names in text and structures them according
        to the entity name schema.

        Args:
            text: The text to extract names from
            title: Optional title/heading that may contain the primary name

        Returns:
            List of name dictionaries with 'kind', 'en', and optionally 'ne' fields

        Examples:
            >>> extractor = NameExtractor()
            >>> names = extractor.extract_names(
            ...     "Ram Chandra Poudel (राम चन्द्र पौडेल) is a politician.",
            ...     title="Ram Chandra Poudel"
            ... )
        """
        names = []

        # Extract primary name from title if available
        if title:
            primary_name = self._structure_name(title.replace("_", " "))
            if primary_name:
                names.append(
                    {
                        "kind": "PRIMARY",
                        "en": primary_name,
                    }
                )

        # Extract names with Nepali variants from text
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if len(match.groups()) >= 2:
                    # Has both English and Nepali
                    english_name = match.group(1)
                    nepali_name = match.group(2)

                    # Check if nepali_name contains Devanagari
                    if any(0x0900 <= ord(c) <= 0x097F for c in nepali_name):
                        name_obj = {
                            "kind": "PRIMARY" if not names else "ALIAS",
                            "en": self._structure_name(english_name),
                            "ne": self._structure_name(nepali_name),
                        }
                        names.append(name_obj)
                elif len(match.groups()) >= 1:
                    # Only English name
                    english_name = match.group(1)
                    if not any(n["en"]["full"] == english_name for n in names):
                        names.append(
                            {
                                "kind": "PRIMARY" if not names else "ALIAS",
                                "en": self._structure_name(english_name),
                            }
                        )

        # Ensure at least one name
        if not names and title:
            names.append(
                {
                    "kind": "PRIMARY",
                    "en": self._structure_name(title.replace("_", " ")),
                }
            )

        return names

    def _structure_name(self, full_name: str) -> Dict[str, str]:
        """Structure a full name into components.

        Args:
            full_name: The full name string

        Returns:
            Dictionary with 'full' and optionally 'first', 'middle', 'last'
        """
        name_parts = full_name.strip().split()

        structured = {"full": full_name.strip()}

        if len(name_parts) == 1:
            structured["given"] = name_parts[0]
        elif len(name_parts) == 2:
            structured["given"] = name_parts[0]
            structured["family"] = name_parts[1]
        elif len(name_parts) >= 3:
            structured["given"] = name_parts[0]
            structured["middle"] = " ".join(name_parts[1:-1])
            structured["family"] = name_parts[-1]

        return structured

    def disambiguate_name(
        self,
        name: str,
        context: str,
    ) -> str:
        """Disambiguate a name using context.

        Uses context to determine the most likely full name when
        multiple possibilities exist.

        Args:
            name: The name to disambiguate
            context: Context text for disambiguation

        Returns:
            Disambiguated name
        """
        # Simple implementation - real version would use LLM
        return name.strip()

    def standardize_name(
        self,
        name: str,
    ) -> str:
        """Standardize a name to a canonical form.

        Normalizes spacing, capitalization, and formatting.

        Args:
            name: The name to standardize

        Returns:
            Standardized name
        """
        # Remove extra whitespace
        name = " ".join(name.split())

        # Capitalize properly
        words = name.split()
        standardized = []

        for word in words:
            # Keep all-caps acronyms
            if word.isupper() and len(word) > 1:
                standardized.append(word)
            else:
                # Capitalize first letter
                standardized.append(word.capitalize())

        return " ".join(standardized)


class AttributeExtractor:
    """Attribute extractor for identifying entity attributes from text.

    Extracts structured attributes like positions, party affiliations,
    dates, and other entity-specific information.

    Attributes:
        attribute_patterns: Patterns for extracting specific attributes
    """

    def __init__(self):
        """Initialize the attribute extractor."""
        # Patterns for extracting attributes
        self.attribute_patterns = {
            "position": [
                r"(?:is|was|served as)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(?:President|Prime Minister|Minister|Deputy|Chief)",
            ],
            "party": [
                r"member of (?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(?:Nepali Congress|CPN-UML|Maoist|Rastriya Prajatantra Party)",
            ],
            "occupation": [
                r"(?:is|was)\s+a\s+([a-z]+)",
                r"(?:politician|lawyer|doctor|engineer|teacher)",
            ],
        }

    def extract_attributes(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Extract entity attributes from text.

        Identifies and extracts structured attributes like positions,
        party affiliations, occupations, and other entity metadata.

        Args:
            text: The text to extract attributes from

        Returns:
            Dictionary of extracted attributes

        Examples:
            >>> extractor = AttributeExtractor()
            >>> attrs = extractor.extract_attributes(
            ...     "Ram Chandra Poudel is the President of Nepal and a member of Nepali Congress."
            ... )
            >>> print(attrs["position"])
            'President'
        """
        attributes = {}

        # Extract position
        if "President" in text:
            attributes["position"] = "President"
        elif "Prime Minister" in text:
            attributes["position"] = "Prime Minister"
        elif "Deputy Prime Minister" in text:
            attributes["position"] = "Deputy Prime Minister"
        elif "Minister" in text:
            attributes["position"] = "Minister"

        # Extract party affiliation
        if "Nepali Congress" in text:
            attributes["party"] = "nepali-congress"
        elif "CPN-UML" in text or "Communist Party" in text:
            attributes["party"] = "cpn-uml"
        elif "Maoist" in text:
            attributes["party"] = "maoist"

        # Extract occupation
        if "politician" in text.lower():
            attributes["occupation"] = "politician"
        elif "lawyer" in text.lower():
            attributes["occupation"] = "lawyer"

        # Extract birth date if present
        birth_date_match = re.search(r"born on ([A-Z][a-z]+ \d{1,2}, \d{4})", text)
        if birth_date_match:
            attributes["birth_date"] = birth_date_match.group(1)

        return attributes

    def extract_temporal_info(
        self,
        text: str,
    ) -> Dict[str, Optional[str]]:
        """Extract temporal information from text.

        Identifies start dates, end dates, and date ranges from text.

        Args:
            text: The text to extract temporal information from

        Returns:
            Dictionary with 'start_date' and 'end_date' keys
        """
        temporal = {
            "start_date": None,
            "end_date": None,
        }

        # Pattern: "from YYYY to YYYY"
        date_range_match = re.search(r"from (\d{4}) to (\d{4})", text)
        if date_range_match:
            temporal["start_date"] = f"{date_range_match.group(1)}-01-01"
            temporal["end_date"] = f"{date_range_match.group(2)}-12-31"

        # Pattern: "since YYYY"
        since_match = re.search(r"since (\d{4})", text)
        if since_match:
            temporal["start_date"] = f"{since_match.group(1)}-01-01"

        # Pattern: "until YYYY"
        until_match = re.search(r"until (\d{4})", text)
        if until_match:
            temporal["end_date"] = f"{until_match.group(1)}-12-31"

        return temporal


class RelationshipExtractor:
    """Relationship extractor for discovering entity relationships from text.

    Analyzes narrative text to identify relationships between entities,
    including relationship types, target entities, and temporal information.

    Attributes:
        relationship_patterns: Patterns for identifying relationship types
    """

    def __init__(self):
        """Initialize the relationship extractor."""
        # Patterns for identifying relationships
        self.relationship_patterns = {
            "MEMBER_OF": [
                r"member of (?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"belongs to (?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ],
            "HELD_POSITION": [
                r"(?:served as|was|is)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ],
            "AFFILIATED_WITH": [
                r"affiliated with (?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"associated with (?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ],
            "WORKED_UNDER": [
                r"under ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"served under ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ],
        }

    def extract_relationships(
        self,
        text: str,
        entity_id: str,
    ) -> List[Dict[str, Any]]:
        """Extract relationships from narrative text.

        Analyzes text to identify relationships between entities, including
        relationship types, target entities, and temporal information.

        Args:
            text: The narrative text to analyze
            entity_id: The source entity ID for extracted relationships

        Returns:
            List of relationship dictionaries

        Examples:
            >>> extractor = RelationshipExtractor()
            >>> rels = extractor.extract_relationships(
            ...     "Ram Chandra Poudel is a member of the Nepali Congress party.",
            ...     "entity:person/ram-chandra-poudel"
            ... )
        """
        relationships = []

        # Extract MEMBER_OF relationships
        if "member of" in text.lower():
            if "Nepali Congress" in text:
                relationships.append(
                    {
                        "type": "MEMBER_OF",
                        "target_entity": {
                            "name": "Nepali Congress",
                            "id": "entity:organization/political_party/nepali-congress",
                        },
                    }
                )

        # Extract HELD_POSITION relationships
        position_keywords = [
            "President",
            "Prime Minister",
            "Deputy Prime Minister",
            "Minister",
            "Chief Justice",
            "Speaker",
        ]

        for keyword in position_keywords:
            if keyword in text:
                rel = {
                    "type": "HELD_POSITION",
                    "target_entity": {
                        "name": keyword,
                    },
                }

                # Extract temporal information
                temporal = self._extract_temporal_from_context(text, keyword)
                if temporal["start_date"]:
                    rel["start_date"] = temporal["start_date"]
                if temporal["end_date"]:
                    rel["end_date"] = temporal["end_date"]

                relationships.append(rel)

        # Extract WORKED_UNDER relationships
        under_match = re.search(
            r"(?:served|worked) under ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text
        )
        if under_match:
            relationships.append(
                {
                    "type": "WORKED_UNDER",
                    "target_entity": {
                        "name": under_match.group(1),
                    },
                }
            )

        return relationships

    def _extract_temporal_from_context(
        self,
        text: str,
        keyword: str,
    ) -> Dict[str, Optional[str]]:
        """Extract temporal information related to a specific keyword.

        Args:
            text: The text to analyze
            keyword: The keyword to find temporal context for

        Returns:
            Dictionary with 'start_date' and 'end_date'
        """
        temporal = {
            "start_date": None,
            "end_date": None,
        }

        # Find the keyword position
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return temporal

        # Look for dates near the keyword (within 100 characters)
        context = text[max(0, keyword_pos - 50) : min(len(text), keyword_pos + 100)]

        # Pattern: "from YYYY to YYYY"
        date_range_match = re.search(r"from (\d{4}) to (\d{4})", context)
        if date_range_match:
            temporal["start_date"] = f"{date_range_match.group(1)}-01-01"
            temporal["end_date"] = f"{date_range_match.group(2)}-12-31"

        return temporal

    def identify_relationship_type(
        self,
        text: str,
    ) -> Optional[str]:
        """Identify the relationship type from text.

        Args:
            text: The text describing the relationship

        Returns:
            Relationship type or None
        """
        text_lower = text.lower()

        if "member of" in text_lower or "belongs to" in text_lower:
            return "MEMBER_OF"
        elif "served as" in text_lower or "held position" in text_lower:
            return "HELD_POSITION"
        elif "affiliated with" in text_lower:
            return "AFFILIATED_WITH"
        elif "worked under" in text_lower or "served under" in text_lower:
            return "WORKED_UNDER"

        return None


class DataQualityAssessor:
    """Data quality assessor for evaluating extracted data.

    Assesses the quality and completeness of extracted entity and
    relationship data, providing quality scores and recommendations.

    Attributes:
        required_fields: Fields required for minimum data quality
        recommended_fields: Fields recommended for good data quality
    """

    def __init__(self):
        """Initialize the data quality assessor."""
        self.required_fields = {
            "person": ["slug", "type", "names"],
            "organization": ["slug", "type", "names"],
            "location": ["slug", "type", "names"],
        }

        self.recommended_fields = {
            "person": ["identifiers", "attributes", "descriptions"],
            "organization": ["identifiers", "attributes", "descriptions"],
            "location": ["identifiers", "attributes", "descriptions"],
        }

    def assess_entity_quality(
        self,
        entity_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess the quality of extracted entity data.

        Evaluates completeness, validity, and quality of entity data.

        Args:
            entity_data: The entity data to assess

        Returns:
            Dictionary containing:
                - quality_score: Overall quality score (0-100)
                - completeness: Completeness score (0-100)
                - issues: List of identified issues
                - recommendations: List of recommendations

        Examples:
            >>> assessor = DataQualityAssessor()
            >>> quality = assessor.assess_entity_quality(entity_data)
            >>> print(quality["quality_score"])
            85
        """
        entity_type = entity_data.get("type", "person")
        issues = []
        recommendations = []

        # Check required fields
        required = self.required_fields.get(entity_type, [])
        missing_required = [f for f in required if f not in entity_data]

        if missing_required:
            issues.append(f"Missing required fields: {', '.join(missing_required)}")

        # Check recommended fields
        recommended = self.recommended_fields.get(entity_type, [])
        missing_recommended = [f for f in recommended if f not in entity_data]

        if missing_recommended:
            recommendations.append(f"Consider adding: {', '.join(missing_recommended)}")

        # Check name quality
        if "names" in entity_data:
            names = entity_data["names"]
            if not names:
                issues.append("No names provided")
            else:
                # Check for PRIMARY name
                primary_names = [n for n in names if n.get("kind") == "PRIMARY"]
                if not primary_names:
                    issues.append("No PRIMARY name specified")

                # Check for Nepali name
                has_nepali = any("ne" in n for n in names)
                if not has_nepali:
                    recommendations.append("Consider adding Nepali name variant")

        # Check identifier quality
        if "identifiers" in entity_data:
            identifiers = entity_data["identifiers"]
            if not identifiers:
                recommendations.append("Consider adding external identifiers")
        else:
            recommendations.append("Consider adding external identifiers")

        # Calculate scores
        required_score = (
            (len(required) - len(missing_required)) / len(required) * 100
            if required
            else 100
        )

        recommended_score = (
            (len(recommended) - len(missing_recommended)) / len(recommended) * 100
            if recommended
            else 100
        )

        # Weighted average: required fields are more important
        quality_score = (required_score * 0.7) + (recommended_score * 0.3)

        # Completeness score
        total_fields = len(required) + len(recommended)
        present_fields = (len(required) - len(missing_required)) + (
            len(recommended) - len(missing_recommended)
        )
        completeness = (present_fields / total_fields * 100) if total_fields > 0 else 0

        return {
            "quality_score": round(quality_score, 1),
            "completeness": round(completeness, 1),
            "issues": issues,
            "recommendations": recommendations,
        }

    def assess_relationship_quality(
        self,
        relationship_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess the quality of extracted relationship data.

        Evaluates completeness and validity of relationship data.

        Args:
            relationship_data: The relationship data to assess

        Returns:
            Dictionary containing quality assessment
        """
        issues = []
        recommendations = []

        # Check required fields
        required_fields = ["type", "target_entity"]
        missing_required = [f for f in required_fields if f not in relationship_data]

        if missing_required:
            issues.append(f"Missing required fields: {', '.join(missing_required)}")

        # Check target entity information
        if "target_entity" in relationship_data:
            target = relationship_data["target_entity"]
            if "name" not in target and "id" not in target:
                issues.append("Target entity missing both name and ID")

        # Check temporal information
        has_temporal = (
            "start_date" in relationship_data or "end_date" in relationship_data
        )
        if not has_temporal:
            recommendations.append("Consider adding temporal information (dates)")

        # Calculate quality score
        quality_score = 100 - (len(issues) * 20) - (len(recommendations) * 5)
        quality_score = max(0, min(100, quality_score))

        return {
            "quality_score": round(quality_score, 1),
            "issues": issues,
            "recommendations": recommendations,
        }


class DataNormalizer:
    """Data normalizer for structuring unstructured data.

    Main class that coordinates all normalization components to extract
    structured entity and relationship data from unstructured text.

    Attributes:
        name_extractor: Name extraction component
        attribute_extractor: Attribute extraction component
        relationship_extractor: Relationship extraction component
        quality_assessor: Data quality assessment component
    """

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the data normalizer.

        Args:
            llm_provider: The LLM provider to use (optional, for future LLM-based extraction)
            llm_config: Configuration dictionary for the LLM provider
        """
        self.llm_provider = llm_provider
        self.llm_config = llm_config or {}

        # Initialize components
        self.name_extractor = NameExtractor()
        self.attribute_extractor = AttributeExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.quality_assessor = DataQualityAssessor()

    def normalize_person_data(
        self,
        raw_data: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:
        """Normalize person data from raw text to entity structure.

        Uses extraction components to build structured entity data from
        unstructured text.

        Args:
            raw_data: Raw data dictionary containing:
                - content: The text content to normalize
                - url: Source URL (optional)
                - title: Source title (optional)
            source: The data source (e.g., "wikipedia")

        Returns:
            Dictionary containing normalized entity data
        """
        content = raw_data.get("content", "")
        title = raw_data.get("title", "")
        url = raw_data.get("url", "")

        # Extract names
        names = self.name_extractor.extract_names(content, title)

        # Generate slug from primary name
        primary_name = names[0]["en"]["full"] if names else title
        slug = self._generate_slug(primary_name)

        # Extract attributes
        attributes = self.attribute_extractor.extract_attributes(content)

        # Build identifiers
        identifiers = []
        if url and source == "wikipedia":
            identifiers.append(
                {
                    "scheme": "wikipedia",
                    "value": title,
                    "url": url,
                }
            )

        # Build normalized entity
        normalized = {
            "slug": slug,
            "type": "person",
            "sub_type": "politician",
            "names": names,
            "identifiers": identifiers,
            "attributes": attributes,
        }

        return normalized

    def extract_relationships(
        self,
        text: str,
        entity_id: str,
    ) -> List[Dict[str, Any]]:
        """Extract relationships from narrative text.

        Args:
            text: The narrative text to analyze
            entity_id: The source entity ID for extracted relationships

        Returns:
            List of relationship dictionaries
        """
        return self.relationship_extractor.extract_relationships(text, entity_id)

    def assess_quality(
        self,
        data: Dict[str, Any],
        data_type: str = "entity",
    ) -> Dict[str, Any]:
        """Assess the quality of extracted data.

        Args:
            data: The data to assess
            data_type: Type of data ("entity" or "relationship")

        Returns:
            Quality assessment dictionary
        """
        if data_type == "entity":
            return self.quality_assessor.assess_entity_quality(data)
        elif data_type == "relationship":
            return self.quality_assessor.assess_relationship_quality(data)
        else:
            return {"quality_score": 0, "issues": ["Unknown data type"]}

    def _generate_slug(self, name: str) -> str:
        """Generate a slug from a name.

        Args:
            name: The name to generate slug from

        Returns:
            Slug string
        """
        # Convert to lowercase
        slug = name.lower()

        # Replace spaces and underscores with hyphens
        slug = slug.replace(" ", "-").replace("_", "-")

        # Remove special characters
        slug = re.sub(r"[^a-z0-9-]", "", slug)

        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)

        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        return slug
