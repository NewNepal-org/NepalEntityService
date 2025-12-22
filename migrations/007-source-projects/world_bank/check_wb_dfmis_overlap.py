#!/usr/bin/env python3
"""
Check for overlap between World Bank and DFMIS project data.

This script uses the ProjectMatcher classes to identify duplicates.

Run: poetry run python migrations/007-source-projects/check_wb_dfmis_overlap.py
"""

import json
from pathlib import Path

from project_matcher import MatchLevel, WorldBankMatcher, get_match_stats


def load_jsonl(filepath: Path) -> list:
    """Load projects from JSONL file."""
    projects = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                projects.append(json.loads(line))
    return projects


def main():
    source_dir = Path(__file__).parent / "source"

    # Load data
    dfmis_file = source_dir / "dfmis_projects.jsonl"
    wb_file = source_dir / "world_bank_projects.jsonl"

    if not dfmis_file.exists():
        print(f"ERROR: DFMIS file not found: {dfmis_file}")
        return

    if not wb_file.exists():
        print(f"ERROR: World Bank file not found: {wb_file}")
        return

    print("Loading project data...")
    dfmis_projects = load_jsonl(dfmis_file)
    wb_projects = load_jsonl(wb_file)

    print(f"  DFMIS projects: {len(dfmis_projects)}")
    print(f"  World Bank projects: {len(wb_projects)}")
    print()

    # Create World Bank matcher with DFMIS as existing projects
    print("=" * 80)
    print("USING WorldBankMatcher CLASS")
    print("=" * 80)
    print()
    print("Matching Strategy (conservative):")
    print("  Level 4 (HIGH):   WB project ID found in DFMIS donor_extensions")
    print("  Level 3 (HIGH):   Exact normalized name match")
    print("  Level 2 (MEDIUM): Fuzzy name (>85%) + amount within 15%")
    print("  Level 1 (LOW):    Fuzzy name (>80%) only")
    print()

    matcher = WorldBankMatcher(dfmis_projects)
    stats = get_match_stats(wb_projects, matcher)

    # Print detailed results
    print("=" * 80)
    print("MATCH RESULTS")
    print("=" * 80)

    # Group by level
    by_level = {
        MatchLevel.HIGH_ID: [],
        MatchLevel.HIGH_NAME: [],
        MatchLevel.MEDIUM: [],
        MatchLevel.LOW: [],
    }

    for item in stats["skipped_projects"]:
        result = item["match_result"]
        by_level[result.level].append(item)

    print(f"\n--- LEVEL 4: WB ID MATCHES ({len(by_level[MatchLevel.HIGH_ID])}) ---")
    for item in by_level[MatchLevel.HIGH_ID][:5]:
        r = item["match_result"]
        print(f"  NEW: {r.new_project_name[:60]}")
        print(f"  EXISTING: {r.existing_project_name[:60]}")
        print(f"  Reason: {r.match_reason}")
        print()

    print(f"\n--- LEVEL 3: EXACT NAME ({len(by_level[MatchLevel.HIGH_NAME])}) ---")
    for item in by_level[MatchLevel.HIGH_NAME][:5]:
        r = item["match_result"]
        print(f"  NEW: {r.new_project_name[:60]}")
        print(f"  EXISTING: {r.existing_project_name[:60]}")
        print()

    print(f"\n--- LEVEL 2: FUZZY + AMOUNT ({len(by_level[MatchLevel.MEDIUM])}) ---")
    for item in by_level[MatchLevel.MEDIUM][:5]:
        r = item["match_result"]
        print(f"  NEW: {r.new_project_name[:55]}")
        print(f"  EXISTING: {r.existing_project_name[:55]}")
        print(f"  Similarity: {r.similarity:.1%}")
        print()

    print(f"\n--- LEVEL 1: FUZZY NAME ONLY ({len(by_level[MatchLevel.LOW])}) ---")
    print("(These may be different projects - additional financing, phases)")
    for item in by_level[MatchLevel.LOW][:10]:
        r = item["match_result"]
        print(f"  NEW: {r.new_project_name[:55]}")
        print(f"  EXISTING: {r.existing_project_name[:55]}")
        print(f"  Similarity: {r.similarity:.1%}")
        print()

    print(f"\n--- NO MATCHES ({len(stats['import_projects'])}) ---")
    print("World Bank projects safe to import (first 20):")
    for p in stats["import_projects"][:20]:
        names = p.get("names", [])
        name = names[0]["en"]["full"] if names else p.get("name", "Unknown")
        amount = p.get("total_commitment", 0) or 0
        stage = p.get("stage", "unknown")
        print(f"  - {name[:65]} (${amount:,.0f}, {stage})")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total World Bank projects: {stats['total']}")
    print(f"  - Level 4 (WB ID match):      {stats['high_id']:3d} - SKIP")
    print(f"  - Level 3 (Exact name):       {stats['high_name']:3d} - SKIP")
    print(f"  - Level 2 (Fuzzy + amount):   {stats['medium']:3d} - SKIP")
    print(f"  - Level 1 (Fuzzy name only):  {stats['low']:3d} - SKIP (conservative)")
    print(f"  - No matches:                 {stats['none']:3d} - IMPORT")
    print()
    print("MIGRATION PLAN:")
    print(f"  - Projects to SKIP:   {stats['to_skip']:3d}")
    print(f"  - Projects to IMPORT: {stats['to_import']:3d}")


if __name__ == "__main__":
    main()
