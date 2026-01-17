from contextlib import contextmanager
from functools import wraps
from typing import Any, Optional, Type, TypeVar

from .archetype import Archetype
from .command_buffer import CommandBuffer
from .component import Component, ComponentRegistry
from .entity_manager import EntityManager
from .event import EventBus
from .query import Query, QueryManager
from .resources import Resources
from .system import System

_SysType = TypeVar("_SysType", bound=System)


class World:
    """Central coordinator for the ECS runtime.

    The World is the composition root for the ECS. It owns the component registry
    and wires together the entity, query, resource, and events. Most gameplay or
    simulation code should interact with the ECS through this object rather than talking
    to managers directly.

    Responsibilities:
      - Create and remove entities.
      - Add, remove, get, and set component data on entities.
      - Build and cache queries over archetypes.
      - Systems: register systems and control their update order.
      - Provide an event bus for event dispatch and async events processing.
      - Store global resources shared across systems.

    Notes:
      - The World owns a single ComponentRegistry instance. All archetype
        signatures are derived from that registry. DO NOT replace the registry
        after the world has created archetypes/entities, as signatures would no
        longer be comparable.
      - This class is currently not thread-safe. Structural changes (creating entities,
        adding/removing components) should be coordinated with iteration if your
        systems perform queries while mutating the world.

    Attributes:
      - systems (list[System]): Registered systems, sorted by priority.
      - event_bus (EventBus): Event dispatcher and async event queue.
      - registry (ComponentRegistry): Assigns component bits used to build archetype
        signatures.
      - query_manager (QueryManager): Caches queries and tracks newly created
        archetypes so queries stay up to date.
      - entities (EntityManager): Creates entities and manages their lifecycle.
      - resources (Resources): Container for global resources.
    """

    def __init__(self):
        self.systems = []
        self._systems_by_type: dict[Type[System], System] = {}
        self.registry = ComponentRegistry()
        self.query_manager = QueryManager(self.registry)
        self.entities = EntityManager(
            self.registry, on_arch_created=self.query_manager.on_arch_created
        )
        self.resources = Resources()
        self.cmd_buffer = CommandBuffer(self)
        self.event_bus = EventBus(self.cmd_buffer)
        self._write_locked = False  # lock structural commands

    @contextmanager
    def write_lock(self):
        try:
            self._write_locked = True
            yield
        finally:
            self._write_locked = False

    @staticmethod
    def _lock_on_sys_update(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._write_locked:
                raise RuntimeError(
                    f"Function {func.__name__} is locked during system update. Please "
                    f"use `world.cmd_buffer.{func.__name__} instead."
                )
            return func(self, *args, **kwargs)

        return wrapper

    def reserve_id(self):
        return self.entities.reserve_id()

    @_lock_on_sys_update
    def create_entity(
        self,
        components_data: dict[Type[Component], Any],
        reserved_id: Optional[int] = None,
    ) -> int:
        """Create a new entity with initial data"""
        return self.entities.add(components_data, reserved_id)

    @_lock_on_sys_update
    def remove_entity(self, entity_id):
        """Remove an entity from the world"""
        self.entities.remove(entity_id)

    @_lock_on_sys_update
    def add_components(self, entity_id, components_data: dict[Type[Component], Any]):
        """Add components to an entity"""
        self.entities.add_components(entity_id, components_data)

    @_lock_on_sys_update
    def remove_components(self, entity_id, components: list[Type[Component]]):
        """Remove components from an entity"""
        return self.entities.remove_components(entity_id, components)

    def get_component(self, entity_id: int, comp_type: Type[Component]) -> Any:
        """Retrieve an entity component value"""
        return self.entities.get_component(entity_id, comp_type)

    def set_component(self, entity_id: int, comp_type: Type[Component], value: Any):
        """Set component value for an entity"""
        self.entities.set_component(entity_id, comp_type, value)

    def query(
        self, include: list[Type[Component]], exclude: list[Type[Component]] = None
    ) -> Query:
        """Query all archetype with a matching composition

        If the query is new, update it with all existing archetypes.

        Args:
            include: list of components that should be in the matched archetypes
            exclude: list of components that should not be in the matched archetypes
        Returns:
            Query object that can return the relevant Archetypes
        """
        q, is_new = self.query_manager.get_query(include, exclude)
        if is_new:
            for arch in self.entities.archetypes.values():
                q.try_add(arch)
        return q

    def register_system(self, system: System) -> None:
        """Register a new system"""
        system.initialize(self)
        self.systems.append(system)
        self._systems_by_type[type(system)] = system
        self.systems.sort(key=lambda s: s.priority)

    def get_system(self, system_type: Type[_SysType]) -> _SysType:
        try:
            return self._systems_by_type.get(system_type)
        except KeyError:
            raise ValueError(f"System {system_type.__name__} is not registered")

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
                with self.write_lock():
                    try:
                        system.update(self, dt)
                    except Exception as e:
                        self.cmd_buffer.clear()
                        system.on_error(self, e)
                self.flush()

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
        with self.write_lock():
            self.event_bus.update()
        self.flush()

    def flush(self):
        """Execute all commands in the command buffer

        Apply all structural changes that are buffered in the command buffer (called
        by a system but not yet executed).
        This happens automatically after each system is updated. this function provides
        a way to manually perform this action to make these changes available to the
        system immediately.

        WARNING: Executing structural commands while iterating over query results may
        result in unexpected behavior and corrupted data. Do not use this function
        unless you know what you are doing.
        """
        self.cmd_buffer.flush()

    def get_archetype(self, entity_id: int) -> Archetype:
        if entity_id not in self.entities.entities_map:
            raise ValueError(f"Entity {entity_id} does not exist")
        return self.entities.entities_map[entity_id][0]
