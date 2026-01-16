from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .query import Query
    from .world import World


class System(ABC):
    """Abstract base class for systems in the ECS framework."""

    # system group that the system belongs to (i.e. render, physics).
    # the World.update() function can update systems of specific groups.
    group: str = "default"

    def __init__(
        self, priority: float = 10.0, enabled: bool = True, name: Optional[str] = None
    ) -> None:
        """Initialize a new system

        Args:
            priority (float): number that dictates the update order of the system.
                higher number means the system will be updated later than systems with
                a lower number. can be a float or negative value, only the differences
                are used.
            enabled: flag that checks if the `update()` function should be called
            name: optional name of the system - class name by default
        """
        self.priority = priority
        self.enabled = enabled
        self.name = name or self.__class__.__name__
        self.queries: dict[str, Query] = {}

    def initialize(self, world: World) -> None:
        """
        Optional hook called when the system is added to the world.
        Use this for one-time setup (queries, resource allocation, caching, etc.).
        """
        pass

    @abstractmethod
    def update(self, world: World, dt: float) -> None:
        """
        Called every frame/tick if the system is enabled.
        Implement your system logic here.
        """
        pass

    def shutdown(self, world: World) -> None:
        """
        Optional hook called when the system is removed from the world,
        or when the world is shutting down.
        Use this to clean up resources.
        """
        pass

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def on_error(self, world: World, ex: Exception) -> None:
        raise ex
