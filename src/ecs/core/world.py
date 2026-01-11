from typing import Any, Optional, Type

from .component import Component, ComponentRegistry
from .entity_manager import EntityManager
from .event import EventBus
from .query import QueryManager
from .resources import Resources
from .system import System


class World:

    def __init__(self):
        self.systems = []
        self.event_bus = EventBus()
        self.registry = ComponentRegistry()
        self.query_manager = QueryManager(self.registry)
        self.entities = EntityManager(
            self.registry, on_arch_created=self.query_manager.on_arch_created
        )
        self.resources = Resources()

    def create_entity(self, components_data: dict[Type[Component], Any]) -> int:
        return self.entities.add(components_data)

    def remove_entity(self, entity_id):
        self.entities.remove(entity_id)

    def add_component(self, entity_id, components_data: dict[Type[Component], Any]):
        self.entities.add_component(entity_id, components_data)

    def remove_components(self, entity_id, components: list[Type[Component]]):
        return self.entities.remove_components(entity_id, components)

    def get_component(self, entity_id: int, comp_type: Type[Component]) -> Any:
        return self.entities.get_component(entity_id, comp_type)

    def set_component(self, entity_id: int, comp_type: Type[Component], value: Any):
        self.entities.set_component(entity_id, comp_type, value)

    def query(
        self, include: list[Type[Component]], exclude: list[Type[Component]] = None
    ):
        q, is_new = self.query_manager.get_query(include, exclude)
        if is_new:
            for arch in self.entities.archetypes.values():
                q.try_add(arch)
        return q

    def register_system(self, system: System) -> None:
        system.initialize(self)
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority)

    def update_systems(self, dt: float, group: Optional[str] = None) -> None:
        """Update the systems in the world

        Calls the update() method of each registered system.
        If a system is disabled - skip the update.
        Optionally - choose a specific group of systems and only update them

        Args:
            dt (float): time since last system update
            group (Optional[str]): name of the groups to update. only systems with
                `system.group == group` will be updated.
                If None - update all systems.
        """
        for system in self.systems:
            if system.enabled and (group is None or system.group == group):
                system.update(self, dt)

    def update(self, dt: float, group: Optional[str] = None) -> None:
        """Update the world

        Calls the update() method of each registered system and of the event bus.
        If a system is disabled - skip the update.
        Optionally - choose a specific group of systems and only update them

        Args:
            dt (float): time since last system update
            group (Optional[str]): name of the groups to update. only systems with
                `system.group == group` will be updated.
                If None - update all systems.
        """
        self.update_systems(dt, group)
        self.event_bus.update()
