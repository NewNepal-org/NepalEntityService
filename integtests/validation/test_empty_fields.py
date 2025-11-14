"""Test for empty/invalid string fields in entities."""

import asyncio
import json
import re
from typing import Any, Dict

import pytest

from nes.database.file_database import FileDatabase


def is_invalid_string(value: str) -> bool:
    """Check if string contains only symbols, whitespace, or placeholder text."""
    if not value or not value.strip():
        return True

    # Check for placeholder patterns like "...", "---", "N/A", etc.
    placeholder_patterns = [
        r"^\.{2,}$",  # dots only
        r"^-{2,}$",  # dashes only
        r"^_{2,}$",  # underscores only
        r"^n/?a$",  # N/A variations
        r"^tbd$",  # to be determined
        r"^null$",  # null string
        r"^none$",  # none string
    ]

    for pattern in placeholder_patterns:
        if re.match(pattern, value.strip().lower()):
            return True

    # Check if string is mostly symbols/whitespace (>80% non-alphanumeric)
    alphanumeric_count = sum(1 for c in value if c.isalnum())
    if len(value) > 0 and alphanumeric_count / len(value) < 0.2:
        return True

    return False


def check_dict_strings(data: Dict[str, Any], path: str = "") -> list:
    """Recursively check dictionary for invalid string values."""
    issues = []

    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key

        if isinstance(value, str) and is_invalid_string(value):
            issues.append(f"{current_path}: '{value}'")
        elif isinstance(value, dict):
            issues.extend(check_dict_strings(value, current_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str) and is_invalid_string(item):
                    issues.append(f"{current_path}[{i}]: '{item}'")
                elif isinstance(item, dict):
                    issues.extend(check_dict_strings(item, f"{current_path}[{i}]"))

    return issues


@pytest.mark.asyncio
async def test_empty_fields():
    """Test all entities for empty/invalid string fields."""
    db = FileDatabase()
    entities = await db.list_entities(limit=100_000)

    print(f"Checking {len(entities)} entities for invalid string fields...")

    batch_size = 1000
    total_issues = []

    for i in range(0, len(entities), batch_size):
        batch = entities[i : i + batch_size]
        batch_issues = []

        for entity in batch:
            entity_json = json.loads(entity.model_dump_json())
            issues = check_dict_strings(entity_json)
            if issues:
                batch_issues.extend([f"{entity.id}: {issue}" for issue in issues])

        total_issues.extend(batch_issues)
        print(
            f"Processed {min(i + batch_size, len(entities))}/{len(entities)} entities, found {len(batch_issues)} issues in this batch"
        )

    print(f"\nTotal issues found: {len(total_issues)}")

    if total_issues:
        print("\nFirst 20 issues:")
        for issue in total_issues[:20]:
            print(f"  {issue}")

        if len(total_issues) > 20:
            print(f"  ... and {len(total_issues) - 20} more")

    return total_issues


if __name__ == "__main__":
    asyncio.run(test_empty_fields())
