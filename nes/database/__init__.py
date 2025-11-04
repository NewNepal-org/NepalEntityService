"""Database package for Nepal Entity Service."""

from .entity_database import EntityDatabase
from .file_database import FileDatabase


def get_database(root_path: str = "entity-db") -> EntityDatabase:
    """Get a database instance.
    
    Args:
        root_path: Root directory for the database files
        
    Returns:
        EntityDatabase instance
    """
    return FileDatabase(root_path)


__all__ = ["EntityDatabase", "FileDatabase", "get_database"]
