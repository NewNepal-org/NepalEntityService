"""File-based implementation of EntityDatabase."""

import json
from pathlib import Path
from typing import List, Optional

from nes.core.models.entity import ENTITY_TYPE_MAP, Entity
from nes.core.models.relationship import Relationship
from nes.core.models.version import Actor, Version

from .entity_database import EntityDatabase


class FileDatabase(EntityDatabase):
    """File-based implementation of EntityDatabase."""

    def __init__(self, root_path: str = "entity-db"):
        self.root_path = Path(root_path)
        self.root_path.mkdir(exist_ok=True)

    def _id_to_path(self, obj_id: str) -> Path:
        file_path = obj_id.replace(":", "/") + ".json"
        return self.root_path / file_path

    def _ensure_dir(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)

    async def put_entity(self, entity: Entity) -> Entity:
        file_path = self._id_to_path(entity.id)
        self._ensure_dir(file_path)
        with open(file_path, "w") as f:
            json.dump(
                entity.model_dump(),
                f,
                default=str,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        return entity

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        file_path = self._id_to_path(entity_id)
        if not file_path.exists():
            return None
        with open(file_path, "r") as f:
            data = json.load(f)
        
        entity_type = data.get("type")
        entity_subtype = data.get("subType")
        type_map = ENTITY_TYPE_MAP.get(entity_type, {})
        entity_class = type_map.get(entity_subtype, type_map.get(None, Entity))
        return entity_class.model_validate(data)

    async def delete_entity(self, entity_id: str) -> bool:
        file_path = self._id_to_path(entity_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def list_entities(
        self,
        limit: int = 100,
        offset: int = 0,
        type: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> List[Entity]:
        # Build search path based on type/subtype
        if subtype and type:
            search_path = self.root_path / "entity" / type / subtype
        elif type:
            search_path = self.root_path / "entity" / type
        else:
            search_path = self.root_path

        entities = []
        for file_path in search_path.rglob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                if "type" in data:
                    entity_type = data.get("type")
                    entity_subtype = data.get("subType")
                    type_map = ENTITY_TYPE_MAP.get(entity_type, {})
                    entity_class = type_map.get(entity_subtype, type_map.get(None, Entity))
                    entities.append(entity_class.model_validate(data))
                    if len(entities) >= limit + offset:
                        break
            except:
                continue
        return entities[offset : offset + limit]

    async def put_relationship(self, relationship: Relationship) -> Relationship:
        file_path = self._id_to_path(relationship.id)
        self._ensure_dir(file_path)
        with open(file_path, "w") as f:
            json.dump(
                relationship.model_dump(),
                f,
                default=str,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        return relationship

    async def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        file_path = self._id_to_path(relationship_id)
        if not file_path.exists():
            return None
        with open(file_path, "r") as f:
            data = json.load(f)
        return Relationship.model_validate(data)

    async def delete_relationship(self, relationship_id: str) -> bool:
        file_path = self._id_to_path(relationship_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def list_relationships(
        self, limit: int = 100, offset: int = 0
    ) -> List[Relationship]:
        relationships = []
        for file_path in self.root_path.rglob("*.json"):
            if len(relationships) >= limit + offset:
                break
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                if "sourceEntityId" in data:
                    relationships.append(Relationship.model_validate(data))
            except:
                continue
        return relationships[offset : offset + limit]

    async def put_version(self, version: Version) -> Version:
        file_path = self._id_to_path(version.id)
        self._ensure_dir(file_path)
        with open(file_path, "w") as f:
            json.dump(
                version.model_dump(),
                f,
                default=str,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        return version

    async def get_version(self, version_id: str) -> Optional[Version]:
        file_path = self._id_to_path(version_id)
        if not file_path.exists():
            return None
        with open(file_path, "r") as f:
            data = json.load(f)
        return Version.model_validate(data)

    async def delete_version(self, version_id: str) -> bool:
        file_path = self._id_to_path(version_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def list_versions(self, limit: int = 100, offset: int = 0) -> List[Version]:
        versions = []
        for file_path in self.root_path.rglob("*.json"):
            if len(versions) >= limit + offset:
                break
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                if "versionNumber" in data:
                    versions.append(Version.model_validate(data))
            except:
                continue
        return versions[offset : offset + limit]

    async def put_actor(self, actor: Actor) -> Actor:
        file_path = self._id_to_path(actor.id)
        self._ensure_dir(file_path)
        with open(file_path, "w") as f:
            json.dump(
                actor.model_dump(),
                f,
                default=str,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        return actor

    async def get_actor(self, actor_id: str) -> Optional[Actor]:
        file_path = self._id_to_path(actor_id)
        if not file_path.exists():
            return None
        with open(file_path, "r") as f:
            data = json.load(f)
        return Actor.model_validate(data)

    async def delete_actor(self, actor_id: str) -> bool:
        file_path = self._id_to_path(actor_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def list_actors(self, limit: int = 100, offset: int = 0) -> List[Actor]:
        actors = []
        for file_path in self.root_path.rglob("*.json"):
            if len(actors) >= limit + offset:
                break
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                if "slug" in data and "name" in data:
                    actors.append(Actor.model_validate(data))
            except:
                continue
        return actors[offset : offset + limit]
