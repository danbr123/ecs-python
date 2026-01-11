from collections import deque
from typing import Any, Callable, Type

import numpy as np

from .archetype import Archetype
from .component import Component, ComponentRegistry


class EntityManager:

    def __init__(
        self,
        component_registry: ComponentRegistry,
        on_arch_created: Callable[[Archetype], Any],
    ):
        """Manage entities lifecycle and creates Archetypes

        The entity manager is responsible for creating and removing entities
        as well as managing their components and associating them with
        specific Archetypes.

        Args:
            component_registry (ComponentRegistry): component registry for archetype
                signature calculation and quick lookup
            on_arch_created (Callable[[Archetype], Any]): hook that is called when creating
                a new archetype - this should be used to update all existing queries.
        """
        self.next_id = 0
        self.entities_map: dict[int, tuple[Archetype, int]] = {}
        self.archetypes: dict[int, Archetype] = {}
        self.registry = component_registry
        self.on_arch_created = on_arch_created

    @staticmethod
    def _validate_data(comp_type: Type[Component], value: Any):
        """Perform validation of data against component schema."""
        if not __debug__:
            return

        val_array = np.asanyarray(value)

        if ((comp_type.shape != (1,) and val_array.shape != comp_type.shape)
                or (comp_type.shape == (1,) and val_array.shape not in [(1,), ()])):
            raise ValueError(
                f"Component {comp_type.__name__} expects shape {comp_type.shape}, "
                f"but got {val_array.shape}."
            )

        if not np.can_cast(val_array.dtype, comp_type.dtype, casting="same_kind"):
            raise TypeError(
                f"Component {comp_type.__name__} expects dtype {comp_type.dtype}, "
                f"but got incompatible dtype {val_array.dtype}."
            )

    def get_archetype(self, components: list[Type[Component]]) -> Archetype:
        components = self.registry.sort_components(components)
        sig = self.registry.get_signature(components)
        if sig not in self.archetypes:
            new_arch = Archetype(components, sig)
            self.on_arch_created(new_arch)
            self.archetypes[sig] = new_arch
        return self.archetypes[sig]

    def assign_id(self):
        ret = self.next_id
        self.next_id += 1
        return ret

    def _remove_and_swap(self, arch: Archetype, row: int):
        swapped = arch.remove_entity(row)
        if swapped != -1:
            self.entities_map[swapped] = (arch, row)

    def add(self, components_data: dict[Type[Component], Any]) -> int:
        for comp_type, value in components_data.items():
            self._validate_data(comp_type, value)

        comp_types = list(components_data.keys())
        archetype = self.get_archetype(comp_types)
        eid = self.assign_id()
        row = archetype.allocate(eid)
        for comp_type, value in components_data.items():
            archetype.storage[comp_type][row] = value
        self.entities_map[eid] = (archetype, row)
        return eid

    def remove(self, entity_id):
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")
        arch, row = self.entities_map.pop(entity_id)
        self._remove_and_swap(arch, row)
        return entity_id

    def add_component(self, entity_id, components_data: dict[Type[Component], Any]):
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")

        for comp_type, value in components_data.items():
            self._validate_data(comp_type, value)

        prev_arch, prev_row = self.entities_map[entity_id]

        types = list(prev_arch.components)
        for comp_type in components_data:
            if comp_type not in types:
                types.append(comp_type)

        new_arch = self.get_archetype(types)
        if new_arch == prev_arch:
            for comp_type, value in components_data.items():
                new_arch.storage[comp_type][prev_row] = value
            return

        new_row = new_arch.allocate(entity_id)
        for comp_type, prev_data in prev_arch.storage.items():
            new_arch.storage[comp_type][new_row] = prev_data[prev_row]
        self._remove_and_swap(prev_arch, prev_row)

        for comp_type, value in components_data.items():
            new_arch.storage[comp_type][new_row] = value
        self.entities_map[entity_id] = (new_arch, new_row)

    def remove_components(self, entity_id, components: list[Type[Component]]):
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")

        prev_arch, prev_row = self.entities_map[entity_id]

        to_remove = set(components)
        types = [c for c in prev_arch.components if c not in to_remove]

        new_arch = self.get_archetype(types)
        if new_arch == prev_arch:
            return

        new_row = new_arch.allocate(entity_id)
        for comp_type, data in new_arch.storage.items():
            data[new_row] = prev_arch.storage[comp_type][prev_row]

        self._remove_and_swap(prev_arch, prev_row)
        self.entities_map[entity_id] = (new_arch, new_row)

    def get_component(self, entity_id: int, comp_type: Type[Component]) -> Any:
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")

        arch, row = self.entities_map[entity_id]
        if comp_type not in arch.components:
            raise ValueError(f"entity {entity_id} does not have component {comp_type.__name__}")
        return arch.storage[comp_type][row]

    def set_component(self, entity_id: int, comp_type: Type[Component], value: Any):
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")
        self._validate_data(comp_type, value)
        arch, row = self.entities_map[entity_id]
        if comp_type in arch.storage:
            arch.storage[comp_type][row] = value
        else:
            self.add_component(entity_id, {comp_type: value})
