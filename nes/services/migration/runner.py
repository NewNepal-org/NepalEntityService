"""
Migration Runner for executing migration scripts.

This module provides the MigrationRunner class which handles:
- Loading and executing migration scripts
- Creating migration contexts for script execution
- Tracking execution statistics (entities/relationships created)
- Error handling and logging
- Deterministic execution (checking for migration logs)
- Storing migration logs for tracking applied migrations
"""

import importlib.util
import inspect
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import List

from nes.database.entity_database import EntityDatabase
from nes.services.migration.context import MigrationContext
from nes.services.migration.manager import MigrationManager
from nes.services.migration.models import Migration, MigrationResult, MigrationStatus
from nes.services.publication.service import PublicationService
from nes.services.scraping.service import ScrapingService
from nes.services.search.service import SearchService

logger = logging.getLogger(__name__)


class MigrationRunner:
    """
    Executes migration scripts and manages migration logs.

    The MigrationRunner is responsible for:
    - Loading migration scripts dynamically
    - Creating execution contexts with service access
    - Executing migration scripts with error handling
    - Tracking execution statistics
    - Checking for migration logs to ensure determinism
    - Storing migration logs for tracking applied migrations
    - Managing batch execution of multiple migrations
    """

    def __init__(
        self,
        publication_service: PublicationService,
        search_service: SearchService,
        scraping_service: ScrapingService,
        db: EntityDatabase,
        migration_manager: MigrationManager,
    ):
        """
        Initialize the Migration Runner.

        Args:
            publication_service: Service for creating/updating entities and relationships
            search_service: Service for searching and querying entities
            scraping_service: Service for data extraction and normalization
            db: Database for direct read access to entities
            migration_manager: Manager for discovering and tracking migrations
        """
        self.publication = publication_service
        self.search = search_service
        self.scraping = scraping_service
        self.db = db
        self.manager = migration_manager

        logger.info("MigrationRunner initialized")

    def create_context(self, migration: Migration) -> MigrationContext:
        """
        Create execution context for migration script.

        The context provides the migration script with:
        - Access to publication, search, and scraping services
        - Access to the database for read operations
        - File reading helpers (CSV, JSON, Excel)
        - Logging mechanism
        - Path to the migration folder

        Args:
            migration: Migration to create context for

        Returns:
            MigrationContext instance ready for script execution

        Example:
            >>> runner = MigrationRunner(...)
            >>> migration = Migration(...)
            >>> context = runner.create_context(migration)
            >>> # Pass context to migration script
            >>> await migrate(context)
        """
        logger.debug(f"Creating context for migration {migration.full_name}")

        context = MigrationContext(
            publication_service=self.publication,
            search_service=self.search,
            scraping_service=self.scraping,
            db=self.db,
            migration_dir=migration.folder_path,
        )

        return context

    def _load_script(self, migration: Migration) -> tuple:
        """
        Load migration script dynamically and validate it.

        This method:
        - Dynamically imports the migration script (migrate.py or run.py)
        - Validates that the script has a migrate() function
        - Validates that the script has required metadata (AUTHOR, DATE, DESCRIPTION)
        - Handles syntax errors gracefully

        Args:
            migration: Migration to load script for

        Returns:
            Tuple of (migrate_function, metadata_dict)

        Raises:
            ValueError: If script is invalid or missing required components
            SyntaxError: If script has syntax errors

        Example:
            >>> runner = MigrationRunner(...)
            >>> migration = Migration(...)
            >>> migrate_func, metadata = runner._load_script(migration)
            >>> await migrate_func(context)
        """
        logger.debug(f"Loading script for migration {migration.full_name}")

        script_path = migration.script_path

        if not script_path.exists():
            raise ValueError(f"Migration script not found: {script_path}")

        # Create a unique module name to avoid conflicts
        module_name = f"migration_{migration.full_name.replace('-', '_')}"

        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None or spec.loader is None:
                raise ValueError(f"Failed to load module spec from {script_path}")

            module = importlib.util.module_from_spec(spec)

            # Add to sys.modules temporarily to support relative imports
            sys.modules[module_name] = module

            try:
                spec.loader.exec_module(module)
            finally:
                # Clean up sys.modules
                if module_name in sys.modules:
                    del sys.modules[module_name]

            logger.debug(f"Successfully loaded module from {script_path}")

        except SyntaxError as e:
            error_msg = (
                f"Syntax error in migration script {migration.full_name}:\n"
                f"  File: {e.filename}\n"
                f"  Line {e.lineno}: {e.text}\n"
                f"  {' ' * (e.offset - 1) if e.offset else ''}^\n"
                f"  {e.msg}"
            )
            logger.error(error_msg)
            raise SyntaxError(error_msg)

        except Exception as e:
            error_msg = f"Failed to load migration script {migration.full_name}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate that the module has a migrate() function
        if not hasattr(module, "migrate"):
            raise ValueError(
                f"Migration script {migration.full_name} must define a 'migrate()' function"
            )

        migrate_func = getattr(module, "migrate")

        # Validate that migrate is a function
        if not callable(migrate_func):
            raise ValueError(
                f"'migrate' in {migration.full_name} must be a callable function"
            )

        # Validate that migrate is async
        if not inspect.iscoroutinefunction(migrate_func):
            raise ValueError(
                f"'migrate()' function in {migration.full_name} must be async "
                "(defined with 'async def')"
            )

        # Extract metadata
        metadata = {
            "author": getattr(module, "AUTHOR", None),
            "date": getattr(module, "DATE", None),
            "description": getattr(module, "DESCRIPTION", None),
        }

        # Validate required metadata
        missing_metadata = []
        if not metadata["author"]:
            missing_metadata.append("AUTHOR")
        if not metadata["date"]:
            missing_metadata.append("DATE")
        if not metadata["description"]:
            missing_metadata.append("DESCRIPTION")

        if missing_metadata:
            raise ValueError(
                f"Migration script {migration.full_name} is missing required metadata: "
                f"{', '.join(missing_metadata)}"
            )

        logger.debug(
            f"Validated migration script {migration.full_name}: "
            f"author={metadata['author']}, date={metadata['date']}"
        )

        return migrate_func, metadata

    async def run_migration(
        self,
        migration: Migration,
        dry_run: bool = True,
        auto_commit: bool = True,
        force: bool = False,
    ) -> MigrationResult:
        """
        Execute a migration script with determinism check.

        This method:
        - Checks if migration already applied before execution
        - Skips execution if migration log exists (returns SKIPPED status)
        - Supports force flag to allow re-execution
        - Executes the migration script with proper context
        - Tracks execution time and statistics
        - Stores migration logs when not in dry-run mode
        - Handles all exceptions gracefully

        Args:
            migration: Migration to execute
            dry_run: If True, don't persist changes or logs (default: True)
            auto_commit: If True, store migration logs after execution (default: True)
            force: If True, allow re-execution of already-applied migrations (default: False)

        Returns:
            MigrationResult with execution details

        Example:
            >>> runner = MigrationRunner(...)
            >>> migration = Migration(...)
            >>> result = await runner.run_migration(migration)
            >>> print(result.status)
            MigrationStatus.COMPLETED
        """
        logger.info(f"Running migration {migration.full_name}")

        # Create result object
        result = MigrationResult(
            migration=migration,
            status=MigrationStatus.RUNNING,
        )

        # Check if migration already applied (determinism check via migration logs)
        if not force:
            is_applied = await self._is_migration_logged(migration)
            if is_applied:
                logger.info(
                    f"Migration {migration.full_name} already applied "
                    "(migration log exists), skipping"
                )
                result.status = MigrationStatus.SKIPPED
                result.logs.append(
                    f"Migration {migration.full_name} already applied, skipping"
                )
                return result

        # If force flag is set and migration was applied, log warning
        if force:
            is_applied = await self._is_migration_logged(migration)
            if is_applied:
                logger.warning(
                    f"Force flag set: re-executing already-applied migration "
                    f"{migration.full_name}"
                )
                result.logs.append(
                    f"WARNING: Force re-execution of already-applied migration"
                )

        # Load migration script
        try:
            migrate_func, metadata = self._load_script(migration)
            logger.debug(f"Loaded migration script {migration.full_name}")
        except Exception as e:
            logger.error(f"Failed to load migration script: {e}")
            result.status = MigrationStatus.FAILED
            result.error = e
            result.logs.append(f"Failed to load migration script: {e}")
            return result

        # Create execution context
        context = self.create_context(migration)

        # Track statistics before execution
        entities_before = await self._count_entities()
        relationships_before = await self._count_relationships()

        # Execute migration
        start_time = time.time()

        try:
            logger.info(f"Executing migration {migration.full_name}...")

            # Execute the migrate() function
            await migrate_func(context)

            # Calculate execution time
            end_time = time.time()
            result.duration_seconds = end_time - start_time

            # Track statistics after execution
            entities_after = await self._count_entities()
            relationships_after = await self._count_relationships()

            result.entities_created = entities_after - entities_before
            result.relationships_created = relationships_after - relationships_before

            # Capture logs from context (extend, don't replace)
            result.logs.extend(context.logs)

            # Mark as completed
            result.status = MigrationStatus.COMPLETED

            logger.info(
                f"Migration {migration.full_name} completed successfully in "
                f"{result.duration_seconds:.1f}s "
                f"(created: {result.entities_created} entities, "
                f"{result.relationships_created} relationships)"
            )

            # Store migration logs if auto_commit is enabled and not dry-run
            if auto_commit and not dry_run:
                try:
                    await self._store_migration_log(migration, result)
                    logger.info(
                        f"Migration log stored for {migration.full_name}"
                    )
                except Exception as log_error:
                    logger.error(f"Failed to store migration log: {log_error}")
                    # Mark migration as failed if log storage fails
                    result.status = MigrationStatus.FAILED
                    result.error = log_error
                    result.logs.append(
                        f"ERROR: Failed to store migration log: {log_error}"
                    )

        except Exception as e:
            # Calculate execution time even on failure
            end_time = time.time()
            result.duration_seconds = end_time - start_time

            # Capture error details
            result.status = MigrationStatus.FAILED
            result.error = e

            # Capture logs from context (extend, don't replace)
            result.logs.extend(context.logs)

            # Add error traceback to logs
            error_traceback = traceback.format_exc()
            result.logs.append(f"ERROR: {e}")
            result.logs.append(f"Traceback:\n{error_traceback}")

            logger.error(
                f"Migration {migration.full_name} failed after "
                f"{result.duration_seconds:.1f}s: {e}\n{error_traceback}"
            )

        return result

    async def _count_entities(self) -> int:
        """
        Count total number of entities in the database.

        Returns:
            Total entity count
        """
        try:
            # Use database's list method with a high limit to get count
            # This is a simple implementation - could be optimized with a dedicated count method
            entities = await self.db.list_entities(limit=1000000)
            return len(entities)
        except Exception as e:
            logger.warning(f"Failed to count entities: {e}")
            return 0

    async def _count_relationships(self) -> int:
        """
        Count total number of relationships in the database.

        Returns:
            Total relationship count
        """
        try:
            # Use database's list method with a high limit to get count
            # This is a simple implementation - could be optimized with a dedicated count method
            relationships = await self.db.list_relationships(limit=1000000)
            return len(relationships)
        except Exception as e:
            logger.warning(f"Failed to count relationships: {e}")
            return 0

    def _get_migration_log_dir(self, migration: Migration) -> Path:
        """
        Get the directory path for storing migration logs.

        Args:
            migration: Migration to get log directory for

        Returns:
            Path to migration log directory
        """
        log_base = self.manager.db_repo_path / "v2" / "migration-logs"
        return log_base / migration.full_name

    async def _is_migration_logged(self, migration: Migration) -> bool:
        """
        Check if a migration has been logged (i.e., already applied).

        Args:
            migration: Migration to check

        Returns:
            True if migration log exists, False otherwise
        """
        log_dir = self._get_migration_log_dir(migration)
        metadata_file = log_dir / "metadata.json"
        return metadata_file.exists()

    async def _store_migration_log(
        self, migration: Migration, result: MigrationResult
    ) -> None:
        """
        Store migration log with metadata and changes.

        Creates a folder structure:
        nes-db/v2/migration-logs/{migration-name}/
            metadata.json - Migration metadata and statistics
            changes.json - List of changes made during migration
            logs.txt - Execution logs

        Args:
            migration: Migration that was executed
            result: Result of migration execution

        Raises:
            IOError: If log storage fails
        """
        import json
        from datetime import datetime

        log_dir = self._get_migration_log_dir(migration)
        
        # Create log directory
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Storing migration log in {log_dir}")

        # Store metadata
        metadata = {
            "migration_name": migration.full_name,
            "author": migration.author,
            "date": migration.date.isoformat() if migration.date else None,
            "description": migration.description,
            "executed_at": datetime.now().isoformat(),
            "duration_seconds": result.duration_seconds,
            "entities_created": result.entities_created,
            "relationships_created": result.relationships_created,
            "status": result.status.value,
        }

        metadata_file = log_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.debug(f"Stored metadata: {metadata_file}")

        # Store changes (placeholder for now - could be enhanced to track actual changes)
        changes = {
            "entities_created": result.entities_created,
            "relationships_created": result.relationships_created,
            "summary": f"Created {result.entities_created} entities and {result.relationships_created} relationships",
        }

        changes_file = log_dir / "changes.json"
        with open(changes_file, "w", encoding="utf-8") as f:
            json.dump(changes, f, indent=2)

        logger.debug(f"Stored changes: {changes_file}")

        # Store execution logs
        logs_file = log_dir / "logs.txt"
        with open(logs_file, "w", encoding="utf-8") as f:
            f.write(f"Migration: {migration.full_name}\n")
            f.write(f"Executed at: {datetime.now().isoformat()}\n")
            f.write(f"Duration: {result.duration_seconds:.1f}s\n")
            f.write(f"\n{'='*80}\n")
            f.write("Execution Logs:\n")
            f.write(f"{'='*80}\n\n")
            for log in result.logs:
                f.write(f"{log}\n")

        logger.debug(f"Stored logs: {logs_file}")
        logger.info(f"Migration log stored successfully for {migration.full_name}")

    async def run_migrations(
        self,
        migrations: List[Migration],
        dry_run: bool = False,
        auto_commit: bool = True,
        stop_on_failure: bool = True,
    ) -> List[MigrationResult]:
        """
        Execute multiple migrations in sequential order.

        This method:
        - Executes migrations in the order provided (typically sorted by prefix)
        - Skips already-applied migrations automatically
        - Can stop on first failure or continue based on flag
        - Returns results for all migrations (executed, skipped, or failed)

        Args:
            migrations: List of migrations to execute (in order)
            dry_run: If True, don't commit changes (default: False)
            auto_commit: If True, commit and push changes after each migration (default: True)
            stop_on_failure: If True, stop on first failure; if False, continue (default: True)

        Returns:
            List of MigrationResult objects, one per migration

        Example:
            >>> runner = MigrationRunner(...)
            >>> migrations = [migration1, migration2, migration3]
            >>> results = await runner.run_migrations(migrations)
            >>> for result in results:
            ...     print(f"{result.migration.full_name}: {result.status}")
        """
        logger.info(f"Running batch of {len(migrations)} migrations")

        results = []

        for i, migration in enumerate(migrations, 1):
            logger.info(
                f"Processing migration {i}/{len(migrations)}: {migration.full_name}"
            )

            # Execute migration
            result = await self.run_migration(
                migration=migration,
                dry_run=dry_run,
                auto_commit=auto_commit,
                force=False,  # Never force in batch mode
            )

            results.append(result)

            # Log result
            if result.status == MigrationStatus.COMPLETED:
                logger.info(
                    f"✓ Migration {migration.full_name} completed successfully "
                    f"({result.entities_created} entities, "
                    f"{result.relationships_created} relationships)"
                )
            elif result.status == MigrationStatus.SKIPPED:
                logger.info(
                    f"⊘ Migration {migration.full_name} skipped (already applied)"
                )
            elif result.status == MigrationStatus.FAILED:
                logger.error(
                    f"✗ Migration {migration.full_name} failed: {result.error}"
                )

                # Stop on failure if flag is set
                if stop_on_failure:
                    logger.error(
                        f"Stopping batch execution due to failure in "
                        f"{migration.full_name}"
                    )
                    break

        # Summary
        completed = sum(1 for r in results if r.status == MigrationStatus.COMPLETED)
        skipped = sum(1 for r in results if r.status == MigrationStatus.SKIPPED)
        failed = sum(1 for r in results if r.status == MigrationStatus.FAILED)

        logger.info(
            f"Batch execution complete: "
            f"{completed} completed, {skipped} skipped, {failed} failed"
        )

        return results


