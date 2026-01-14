from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type

from .component import Component

if TYPE_CHECKING:
    from .world import World


class CommandBuffer:
    def __init__(self, world: World):
        self.world = world
        self.commands = []
        self._reserved_ids = []

    def create_entity(self, components_data: dict[Type[Component], Any]):
        """Create a new entity with initial data"""
        entity_id = self.world.reserve_id()
        self.commands.append(("create_entity", components_data, entity_id))
        self._reserved_ids.append(entity_id)
        return entity_id

    def remove_entity(self, entity_id):
        """Remove an entity from the world"""
        self.commands.append(("remove_entity", entity_id))

    def add_components(self, entity_id, components_data: dict[Type[Component], Any]):
        """Add components to an entity"""
        self.commands.append(("add_components", entity_id, components_data))

    def remove_components(self, entity_id, components: list[Type[Component]]):
        """Remove components from an entity"""
        self.commands.append(("remove_components", entity_id, components))

    def flush(self):
        # TODO - group operations
        try:
            for cmd, *args in self.commands:
                if cmd == "create_entity":
                    self.world.entities.add(*args)
                elif cmd == "remove_entity":
                    self.world.entities.remove(*args)
                elif cmd == "add_components":
                    self.world.entities.add_components(*args)
                elif cmd == "remove_components":
                    self.world.entities.remove_components(*args)
        finally:
            self._reserved_ids = []
            self.commands = []

    def clear(self):
        self.world.entities.deregister_reserved_ids(self._reserved_ids)
        self._reserved_ids = []
        self.commands = []
