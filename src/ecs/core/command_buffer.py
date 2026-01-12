from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Type

from .component import Component

if TYPE_CHECKING:
    from .world import World


class CommandBuffer:
    def __init__(self, world: World):
        self.world = world
        self.commands = []

    def create_entity(self, components_data: dict[Type[Component], Any]):
        """Create a new entity with initial data"""
        entity_id = self.world.reserve_id()
        self.commands.append(("create_entity", components_data, entity_id))
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

    @contextmanager
    def redirect_commands(self):
        _prev = {
            "create_entity": self.world.create_entity,
            "remove_entity": self.world.remove_entity,
            "add_components": self.world.add_components,
            "remove_components": self.world.remove_components,
        }
        try:
            self.world.create_entity = self.create_entity
            self.world.remove_entity = self.remove_entity
            self.world.add_components = self.add_components
            self.world.remove_components = self.remove_components
            yield
        finally:
            self.world.create_entity = _prev["create_entity"]
            self.world.remove_entity = _prev["remove_entity"]
            self.world.add_components = _prev["add_components"]
            self.world.remove_components = _prev["remove_components"]

    def flush(self):
        # TODO - group operations
        for cmd, *args in self.commands:
            if cmd == "create_entity":
                self.world.create_entity(*args)
            elif cmd == "remove_entity":
                self.world.remove_entity(*args)
            elif cmd == "add_components":
                self.world.add_components(*args)
            elif cmd == "remove_components":
                self.world.remove_components(*args)
        self.commands = []
