from typing import Any, Callable, Optional, Type

import numpy as np

from .archetype import Archetype
from .component import Component, ComponentRegistry


class PendingEntityException(Exception):
    pass


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
            on_arch_created (Callable[[Archetype], Any]): hook that is called when
                creating a new archetype - this should be used to update all existing
                queries.
        """
        self.next_id = 0
        self.entities_map: dict[int, tuple[Optional[Archetype], Optional[int]]] = {}
        self.archetypes: dict[int, Archetype] = {}
        self.registry = component_registry
        self.on_arch_created = on_arch_created

    @staticmethod
    def _validate_data(comp_type: Type[Component], value: Any):
        """Perform validation of data against component schema."""
        if not __debug__:
            return

        val_array = np.asanyarray(value)

        if (comp_type.shape != (1,) and val_array.shape != comp_type.shape) or (
            comp_type.shape == (1,) and val_array.shape not in [(1,), ()]
        ):
            raise ValueError(
                f"Component {comp_type.__name__} expects shape {comp_type.shape}, "
                f"but got {val_array.shape}."
            )

        if not np.can_cast(val_array.dtype, comp_type.dtype, casting="same_kind"):
            raise TypeError(
                f"Component {comp_type.__name__} expects dtype {comp_type.dtype}, "
                f"but got incompatible dtype {val_array.dtype}."
            )

    def _assign_id(self):
        """Assign unique entity id"""
        ret = self.next_id
        self.next_id += 1
        return ret

    def _remove_and_swap(self, arch: Archetype, row: int):
        """Remove entity from archetype by row

        After the removal, the archetype fills the empty row with
        a different entity id to maintain density, so the function
        also updates the row in the entities_map.

        Args:
            arch (Archetype): the archetype to remove the entity from
            row (int): the *row* of the entity to remove from the archetype
        """
        swapped = arch.remove_entity(row)
        if swapped != -1:
            self.entities_map[swapped] = (arch, row)

    def get_archetype(self, components: list[Type[Component]]) -> Archetype:
        """Get archetype for a given component composition

        If an archetype does not exist yet, create it.
        Use the archetype signature for efficient lookup.

        Args:
            components (list[Type[Component]]): list of components
        Returns:
            archetype (Archetype): an archetype that matches the component composition
        """
        components = self.registry.sort_components(components)
        sig = self.registry.get_signature(components)
        if sig not in self.archetypes:
            new_arch = Archetype(components, sig)
            self.on_arch_created(new_arch)
            self.archetypes[sig] = new_arch
        return self.archetypes[sig]

    def reserve_id(self):
        """Reserve an id for an entity without creating it"""
        eid = self._assign_id()
        self.entities_map[eid] = (None, None)
        return eid

    def deregister_reserved_ids(self, ids: list[int]):
        for eid in ids:
            self.entities_map.pop(eid, None)

    def add(
        self,
        components_data: dict[Type[Component], Any],
        reserved_id: Optional[int] = None,
    ) -> int:
        """Create a new entity with given components

        Calculate the matching archetype for the entity based on the components
        composition, then insert the entity and its component data to the
        archetype storage.
        """
        for comp_type, value in components_data.items():
            self._validate_data(comp_type, value)
        if reserved_id is not None:
            if reserved_id not in self.entities_map:
                raise ValueError(f"entity_id {reserved_id} was not reserved")
            elif self.entities_map[reserved_id][0] is not None:
                raise ValueError(f"entity_id {reserved_id} already exists")
        comp_types = list(components_data.keys())
        archetype = self.get_archetype(comp_types)
        eid = reserved_id or self._assign_id()
        row = archetype.allocate(eid)
        for comp_type, value in components_data.items():
            archetype.storage[comp_type][row] = value
        self.entities_map[eid] = (archetype, row)
        return eid

    def remove(self, entity_id):
        """Remove an entity

        Remove the entity from its archetype and from the entities_map.
        if the entity doesn't exist - raise an exception.

        Args:
            entity_id (int): the entity to remove
        Returns:
            entity_id (int): the removed entity
        """
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")
        arch, row = self.entities_map.pop(entity_id)
        if arch is None:  # entity was reserved but never created
            return entity_id
        self._remove_and_swap(arch, row)
        return entity_id

    def add_components(self, entity_id, components_data: dict[Type[Component], Any]):
        """Add a components to an existing entity

        Calculate the new archetype for the entity based on the new components
        composition, then:
        - Add the entity to the new archetype
        - Copy existing entity data from the previous archetype to the new one
        - Remove the entity from the old archetype
        - add the new component data to the new archetype

        If all components already exist (archetype doesn't change) - this function
        behaves similarly to multiple calls of `EntityManager.set_component`

        if the entity doesn't exist - raise an exception.

        Note:
            IMPORTANT: Since moving entities between archetypes is relatively
            inefficient, it is recommended to add all new components in a single call
            when possible.
            in general, if a component is expected to be added/removed frequently, it
            is recommended to use a flag component that enables/disables it instead
            of actively removing it.

        Args:
            entity_id (int): the entity to add the new components to
            components_data (dict[Type[Component], Any]): dictionary of {type: data}
                where data is a numpy array or scalar with a shape matching the
                component schema.
        """
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")

        for comp_type, value in components_data.items():
            self._validate_data(comp_type, value)

        prev_arch, prev_row = self.entities_map[entity_id]

        if prev_arch is None:  # entity was reserved but never created
            raise RuntimeError("Attempted to structurally modify a pending entity")

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
        """Remove components from an existing entity

        Remove components from an entity by deleting it from its archetype
        and adding it to a new archetype that matches the new component composition.

        if the entity doesn't exist - raise an exception.

        Note:
            this operation changes the archetype and copies the entity data and
            is therefore relatively inefficient. see docstring in
            `EntityManager.add_components` for more information and best practices.
        """
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")

        prev_arch, prev_row = self.entities_map[entity_id]

        if prev_arch is None:  # entity was reserved but never created
            raise RuntimeError("Attempted to structurally modify a pending entity")

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
        """Get the value of a specific component of an entity

        if the entity doesn't exist - raise an exception.

        Args:
            entity_id (int): the entity to get the component value for
            comp_type (Type[Component]): the type of component to get
        Returns:
            value: a scalar or numpy array with the component value

        Raises:
            ValueError: if the entity doesn't exist or doesn't have the component
            PendingEntityException: if the entity is pending
        """
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")

        arch, row = self.entities_map[entity_id]

        if arch is None:  # entity was reserved but never created
            raise PendingEntityException(f"entity_id {entity_id} is still pending")

        if comp_type not in arch.components:
            raise ValueError(
                f"entity {entity_id} does not have component {comp_type.__name__}"
            )
        return arch.storage[comp_type][row]

    def set_component(self, entity_id: int, comp_type: Type[Component], value: Any):
        """Set the value for a specific component of an entity

        New value must match the component schema.
        if the entity doesn't exist - raise an exception.

        Note:
            it is not recommended to use this function to add components to an entity,
            use `EntityManager.add_components` instead.

        Args:
            entity_id (int): the entity to set the component value for
            comp_type (Type[Component]): the type of component to set
            value (Any): a scalar or numpy array with the component value

        Raises:
            ValueError: if the entity doesn't exist or doesn't have the component
            PendingEntityException: if the entity is pending

        """
        if entity_id not in self.entities_map:
            raise ValueError(f"entity_id {entity_id} does not exist")
        self._validate_data(comp_type, value)
        arch, row = self.entities_map[entity_id]

        if arch is None:  # entity was reserved but never created
            raise PendingEntityException(f"entity_id {entity_id} is still pending")

        if comp_type not in arch.storage:
            raise ValueError(
                f"entity {entity_id} does not have component {comp_type.__name__}"
            )
        arch.storage[comp_type][row] = value
