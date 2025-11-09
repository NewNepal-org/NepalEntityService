"""
Data models for the migration system.

This module defines the core data structures used throughout the migration system,
including Migration, MigrationResult, and MigrationStatus.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class MigrationStatus(str, Enum):
    """Status of a migration execution."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Migration:
    """
    Represents a migration folder.

    A migration is a versioned folder containing an executable Python script
    and supporting files (CSVs, Excel, README, etc.) that applies a specific
    set of data changes to the Entity Database.
    """

    prefix: int
    """Numeric prefix determining execution order (e.g., 0, 1, 2)."""

    name: str
    """Descriptive name of the migration (e.g., 'initial-locations')."""

    folder_path: Path
    """Full path to the migration folder."""

    script_path: Path
    """Path to the main migration script (migrate.py or run.py)."""

    readme_path: Optional[Path] = None
    """Path to README.md if it exists."""

    author: Optional[str] = None
    """Author from migration metadata (AUTHOR constant in script)."""

    date: Optional[datetime] = None
    """Date from migration metadata (DATE constant in script)."""

    description: Optional[str] = None
    """Description from migration metadata (DESCRIPTION constant in script)."""

    @property
    def full_name(self) -> str:
        """
        Returns formatted name like '000-initial-locations'.

        This is the canonical identifier for the migration used in
        Git commits, CLI commands, and tracking.
        """
        return f"{self.prefix:03d}-{self.name}"

    def __str__(self) -> str:
        """String representation of the migration."""
        return self.full_name

    def __repr__(self) -> str:
        """Detailed representation of the migration."""
        return (
            f"Migration(prefix={self.prefix}, name='{self.name}', "
            f"folder_path='{self.folder_path}')"
        )


@dataclass
class MigrationResult:
    """
    Result of a migration execution.

    Contains execution status, statistics, timing information, and any errors
    that occurred during migration execution.
    """

    migration: Migration
    """The migration that was executed."""

    status: MigrationStatus = MigrationStatus.RUNNING
    """Current status of the migration execution."""

    duration_seconds: float = 0.0
    """Total execution time in seconds."""

    entities_created: int = 0
    """Number of entities created during migration."""

    entities_updated: int = 0
    """Number of entities updated during migration."""

    relationships_created: int = 0
    """Number of relationships created during migration."""

    relationships_updated: int = 0
    """Number of relationships updated during migration."""

    versions_created: int = 0
    """Number of version files created during migration."""

    error: Optional[Exception] = None
    """Exception that caused the migration to fail, if any."""

    logs: List[str] = field(default_factory=list)
    """Log messages generated during migration execution."""

    git_commit_sha: Optional[str] = None
    """SHA of the Git commit in the Database Repository (if persisted)."""

    def __str__(self) -> str:
        """String representation of the result."""
        if self.status == MigrationStatus.COMPLETED:
            return (
                f"Migration {self.migration.full_name} completed successfully "
                f"in {self.duration_seconds:.1f}s "
                f"(created: {self.entities_created} entities, "
                f"{self.relationships_created} relationships)"
            )
        elif self.status == MigrationStatus.FAILED:
            return (
                f"Migration {self.migration.full_name} failed "
                f"after {self.duration_seconds:.1f}s: {self.error}"
            )
        elif self.status == MigrationStatus.SKIPPED:
            return f"Migration {self.migration.full_name} skipped (already applied)"
        else:
            return f"Migration {self.migration.full_name} is {self.status}"

    def __repr__(self) -> str:
        """Detailed representation of the result."""
        return (
            f"MigrationResult(migration={self.migration.full_name}, "
            f"status={self.status}, duration={self.duration_seconds:.1f}s)"
        )
