"""Configuration for Nepal Entity Service v2."""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for nes2."""

    # Default database path for v2
    DEFAULT_DB_PATH = "nes-db/v2"
    
    # Global instances for database and services
    _database: Optional["EntityDatabase"] = None
    _search_service: Optional["SearchService"] = None
    _publication_service: Optional["PublicationService"] = None

    @classmethod
    def get_db_path(cls, override_path: Optional[str] = None) -> Path:
        """Get the database path.

        Args:
            override_path: Optional path to override the default database path

        Returns:
            Path object for the database directory
        """
        if override_path:
            return Path(override_path)

        # Check for environment variable
        env_path = os.getenv("NES2_DB_PATH")
        if env_path:
            return Path(env_path)

        # Use default path
        return Path(cls.DEFAULT_DB_PATH)

    @classmethod
    def ensure_db_path_exists(cls, db_path: Optional[Path] = None) -> Path:
        """Ensure the database path exists, creating it if necessary.

        Args:
            db_path: Optional database path, uses default if not provided

        Returns:
            Path object for the database directory
        """
        if db_path is None:
            db_path = cls.get_db_path()

        db_path.mkdir(parents=True, exist_ok=True)
        return db_path
    
    @classmethod
    def initialize_database(cls, base_path: str = "./nes-db/v2") -> "EntityDatabase":
        """Initialize the global database instance.
        
        Args:
            base_path: Path to the database directory
            
        Returns:
            Initialized database instance
        """
        from nes2.database.file_database import FileDatabase
        
        cls._database = FileDatabase(base_path=base_path)
        logger.info(f"Database initialized at {base_path}")
        
        return cls._database

    @classmethod
    def get_database(cls) -> "EntityDatabase":
        """Get the global database instance.
        
        Returns:
            EntityDatabase instance
            
        Raises:
            RuntimeError: If database is not initialized
        """
        if cls._database is None:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        return cls._database

    @classmethod
    def get_search_service(cls) -> "SearchService":
        """Get or create the global search service instance.
        
        Returns:
            SearchService instance
        """
        if cls._search_service is None:
            from nes2.services.search import SearchService
            
            db = cls.get_database()
            cls._search_service = SearchService(database=db)
            logger.info("Search service initialized")
        
        return cls._search_service

    @classmethod
    def get_publication_service(cls) -> "PublicationService":
        """Get or create the global publication service instance.
        
        Returns:
            PublicationService instance
        """
        if cls._publication_service is None:
            from nes2.services.publication import PublicationService
            
            db = cls.get_database()
            cls._publication_service = PublicationService(database=db)
            logger.info("Publication service initialized")
        
        return cls._publication_service

    @classmethod
    def cleanup(cls):
        """Clean up global instances on shutdown."""
        logger.info("Cleaning up global instances")
        cls._database = None
        cls._search_service = None
        cls._publication_service = None


# Global configuration instance
config = Config()
