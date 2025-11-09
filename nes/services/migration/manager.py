"""
Migration Manager for discovering and tracking migrations.

This module provides the MigrationManager class which handles:
- Discovery of migrations from the migrations/ directory
- Checking for migration logs to determine applied migrations
- Determining which migrations are pending (not yet applied)
"""

import ast
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from nes.services.migration.models import Migration
from nes.services.migration.validation import validate_migration_naming

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages migration discovery and tracking.

    The MigrationManager is responsible for:
    - Discovering migrations in the migrations/ directory
    - Checking migration logs to find applied migrations
    - Determining which migrations are pending (not yet applied)
    - Providing migration metadata for display and execution
    """

    def __init__(self, migrations_dir: Path, db_repo_path: Path):
        """
        Initialize the Migration Manager.

        Args:
            migrations_dir: Path to the migrations directory (e.g., ./migrations/)
            db_repo_path: Path to the Database Repository (e.g., ./nes-db/)
        """
        self.migrations_dir = Path(migrations_dir)
        self.db_repo_path = Path(db_repo_path)
        self._applied_cache: Optional[List[str]] = None

        logger.info(
            f"MigrationManager initialized: "
            f"migrations_dir={self.migrations_dir}, "
            f"db_repo_path={self.db_repo_path}"
        )

    async def discover_migrations(self) -> List[Migration]:
        """
        Discover all migrations in the migrations directory.

        Scans the migrations/ directory for folders matching the NNN-* pattern,
        sorts them by numeric prefix, and loads metadata from script files.

        Returns:
            List of Migration objects sorted by prefix

        Example:
            >>> manager = MigrationManager(Path("migrations"), Path("nes-db"))
            >>> migrations = await manager.discover_migrations()
            >>> print(migrations[0].full_name)
            '000-initial-locations'
        """
        logger.info(f"Discovering migrations in {self.migrations_dir}")

        if not self.migrations_dir.exists():
            logger.warning(
                f"Migrations directory does not exist: {self.migrations_dir}"
            )
            return []

        migrations = []

        # Scan for migration folders
        for folder_path in self.migrations_dir.iterdir():
            if not folder_path.is_dir():
                continue

            folder_name = folder_path.name

            # Skip hidden directories and __pycache__
            if folder_name.startswith(".") or folder_name == "__pycache__":
                continue

            # Validate naming convention
            validation_result = validate_migration_naming(folder_name)
            if not validation_result.is_valid:
                logger.warning(
                    f"Skipping invalid migration folder '{folder_name}': "
                    f"{', '.join(validation_result.errors)}"
                )
                continue

            # Extract prefix and name
            match = re.match(r"^(\d{3})-(.+)$", folder_name)
            if not match:
                # This shouldn't happen if validation passed, but be defensive
                logger.warning(f"Skipping folder with unexpected format: {folder_name}")
                continue

            prefix_str, name = match.groups()
            prefix = int(prefix_str)

            # Find the main script file
            script_path = folder_path / "migrate.py"
            if not script_path.exists():
                script_path = folder_path / "run.py"

            if not script_path.exists():
                logger.warning(
                    f"Skipping migration folder '{folder_name}': "
                    "no migrate.py or run.py found"
                )
                continue

            # Find README
            readme_path = folder_path / "README.md"
            if not readme_path.exists():
                readme_path = None

            # Load metadata from script
            metadata = self._load_migration_metadata(script_path)

            # Create Migration object
            migration = Migration(
                prefix=prefix,
                name=name,
                folder_path=folder_path,
                script_path=script_path,
                readme_path=readme_path,
                author=metadata.get("author"),
                date=metadata.get("date"),
                description=metadata.get("description"),
            )

            migrations.append(migration)
            logger.debug(f"Discovered migration: {migration.full_name}")

        # Sort by prefix
        migrations.sort(key=lambda m: m.prefix)

        logger.info(f"Discovered {len(migrations)} migrations")
        return migrations

    def _load_migration_metadata(self, script_path: Path) -> dict:
        """
        Load metadata from a migration script.

        Extracts AUTHOR, DATE, and DESCRIPTION constants from the script
        using AST parsing.

        Args:
            script_path: Path to the migration script

        Returns:
            Dictionary with 'author', 'date', and 'description' keys
        """
        metadata = {"author": None, "date": None, "description": None}

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(script_path))

            # Extract module-level assignments
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "AUTHOR":
                                if isinstance(node.value, ast.Constant):
                                    metadata["author"] = node.value.value
                                elif isinstance(node.value, ast.Str):
                                    metadata["author"] = node.value.s

                            elif target.id == "DATE":
                                if isinstance(node.value, ast.Constant):
                                    date_str = node.value.value
                                elif isinstance(node.value, ast.Str):
                                    date_str = node.value.s
                                else:
                                    continue

                                # Try to parse date
                                try:
                                    metadata["date"] = datetime.strptime(
                                        date_str, "%Y-%m-%d"
                                    )
                                except ValueError:
                                    logger.warning(
                                        f"Invalid DATE format in {script_path}: {date_str}"
                                    )

                            elif target.id == "DESCRIPTION":
                                if isinstance(node.value, ast.Constant):
                                    metadata["description"] = node.value.value
                                elif isinstance(node.value, ast.Str):
                                    metadata["description"] = node.value.s

        except Exception as e:
            logger.warning(f"Failed to load metadata from {script_path}: {e}")

        return metadata

    async def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migration names by checking migration logs.

        This checks the nes-db/v2/migration-logs directory for migration
        log folders. Each folder with a metadata.json file indicates that
        the migration has been applied.

        The results are cached to avoid repeated filesystem queries. Call
        clear_cache() to force a refresh.

        Returns:
            List of migration names that have been applied (e.g., ['000-initial-locations'])

        Example:
            >>> manager = MigrationManager(Path("migrations"), Path("nes-db"))
            >>> applied = await manager.get_applied_migrations()
            >>> print(applied)
            ['000-initial-locations', '001-political-parties']
        """
        # Return cached result if available
        if self._applied_cache is not None:
            logger.debug(
                f"Returning cached applied migrations: {len(self._applied_cache)} migrations"
            )
            return self._applied_cache

        logger.info(f"Checking migration logs in {self.db_repo_path}/v2/migration-logs")

        # Check if database repository exists
        if not self.db_repo_path.exists():
            logger.warning(f"Database repository does not exist: {self.db_repo_path}")
            self._applied_cache = []
            return self._applied_cache

        # Check migration logs directory
        migration_logs_dir = self.db_repo_path / "v2" / "migration-logs"
        if not migration_logs_dir.exists():
            logger.info(f"Migration logs directory does not exist: {migration_logs_dir}")
            self._applied_cache = []
            return self._applied_cache

        try:
            applied = []
            
            # Scan migration logs directory for migration folders
            for log_folder in migration_logs_dir.iterdir():
                if not log_folder.is_dir():
                    continue
                
                # Check if metadata.json exists (indicates completed migration)
                metadata_file = log_folder / "metadata.json"
                if metadata_file.exists():
                    migration_name = log_folder.name
                    applied.append(migration_name)
                    logger.debug(f"Found applied migration: {migration_name}")

            # Cache the results
            self._applied_cache = applied
            logger.info(f"Found {len(applied)} applied migrations in logs")

            return applied

        except Exception as e:
            logger.error(f"Unexpected error checking migration logs: {e}")
            self._applied_cache = []
            return self._applied_cache

    def clear_cache(self) -> None:
        """
        Clear the cached list of applied migrations.

        Call this method to force a refresh of the applied migrations list
        from migration logs on the next call to get_applied_migrations().
        """
        logger.debug("Clearing applied migrations cache")
        self._applied_cache = None

    async def get_pending_migrations(self) -> List[Migration]:
        """
        Get migrations that haven't been applied yet.

        Returns only migrations that don't have migration logs in the
        nes-db/v2/migration-logs directory.

        Returns:
            List of Migration objects that are pending (not yet applied)

        Example:
            >>> manager = MigrationManager(Path("migrations"), Path("nes-db"))
            >>> pending = await manager.get_pending_migrations()
            >>> for migration in pending:
            ...     print(migration.full_name)
            '002-update-names'
            '003-add-relationships'
        """
        logger.info("Determining pending migrations")

        # Get all migrations
        all_migrations = await self.discover_migrations()
        logger.debug(f"Total migrations discovered: {len(all_migrations)}")

        # Get applied migrations
        applied = await self.get_applied_migrations()
        logger.debug(f"Applied migrations: {len(applied)}")

        # Filter to only pending migrations
        pending = []
        for migration in all_migrations:
            if migration.full_name not in applied:
                pending.append(migration)
                logger.debug(f"Pending migration: {migration.full_name}")

        logger.info(f"Found {len(pending)} pending migrations")
        return pending

    async def is_migration_applied(self, migration: Migration) -> bool:
        """
        Check if a specific migration has been applied.

        Args:
            migration: Migration to check

        Returns:
            True if the migration has been applied (log exists), False otherwise

        Example:
            >>> manager = MigrationManager(Path("migrations"), Path("nes-db"))
            >>> migration = Migration(prefix=0, name="initial-locations", ...)
            >>> is_applied = await manager.is_migration_applied(migration)
            >>> print(is_applied)
            True
        """
        applied = await self.get_applied_migrations()
        is_applied = migration.full_name in applied

        logger.debug(
            f"Migration {migration.full_name} is "
            f"{'applied' if is_applied else 'pending'}"
        )

        return is_applied

    async def get_migration_by_name(self, name: str) -> Optional[Migration]:
        """
        Get a specific migration by its full name.

        Args:
            name: Full migration name (e.g., '000-initial-locations')

        Returns:
            Migration object if found, None otherwise

        Example:
            >>> manager = MigrationManager(Path("migrations"), Path("nes-db"))
            >>> migration = await manager.get_migration_by_name("000-initial-locations")
        """
        migrations = await self.discover_migrations()

        for migration in migrations:
            if migration.full_name == name:
                return migration

        return None
