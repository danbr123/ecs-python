from typing import Type

import numpy as np

from .component import Component, TagComponent


class Archetype:
    def __init__(
        self,
        components: list[Type[Component]],
        signature: int,
        initial_capacity: int = 256,
    ):
        """Represents a composition of components and stores components data.

        An archetype stores and manages the component data of entities.
        Each archetype represents a specific composition of components, and contains
        the data of all the entities with that specific composition.

        Each archetype has a unique signature per World (calculated by a component
        registry), that is used to efficiently find the archetype of an entity based on
        its components.

        The components data is stored in dense numpy arrays that can be operated on in
        bulk. The arrays are indexed by an internal row_id that is linked to the
        entity_id with an internal mapping. on entity removal, the row of the last
        entity in the array is swapped to maintain density.

        Note:
            The archetype is not responsible for inserting the entity data into the
            arrays, this is done by the EntityManager to allow efficient numpy to numpy
            array copying between archetypes.

        Args:
            components: list of component types that the archetype represents
            signature: the calculated signature of the archetype
            initial_capacity: the initial length of the arrays. the capacity is scaled
                up automatically when needed, but does not scale down.
        """
        self.signature = signature
        self.components = set(components)
        self._capacity = initial_capacity
        self.storage: dict[Type[Component], np.ndarray] = {
            c: np.empty((self._capacity, *c.shape), dtype=c.dtype)
            for c in components
            if not issubclass(c, TagComponent)
        }
        self.entity_ids = np.full(self._capacity, -1, dtype=np.int64)
        self._length = 0

    def __len__(self) -> int:
        return self._length

    def increase_capacity(self):
        """Double the capacity of the archetype arrays"""
        new_capacity = self._capacity * 2
        new_entities = np.full(new_capacity, -1, dtype=np.int64)
        new_entities[: self._length] = self.entity_ids[: self._length]
        self.entity_ids = new_entities

        for comp, data in self.storage.items():
            _new_data = np.empty((new_capacity, *data.shape[1:]), dtype=data.dtype)
            _new_data[: self._length] = data[: self._length]
            self.storage[comp] = _new_data
        self._capacity = new_capacity

    def allocate(self, entity_id: int) -> int:
        """Add a new entity to the archetype

        Add the entity to the mapping and allocate a row.
        This function DOES NOT insert entity data, this is performed by the
        EntityManager.
        The function returns the row of the entity id within the archetype storage.
        This row is used by the EntityManager to locate the entity inside the Archetype.

        Args:
            entity_id (int): entity_id to add
        Returns:
            row (int): the row of the entity id
        """
        if self._length >= self._capacity:
            self.increase_capacity()
        row = self._length
        self.entity_ids[row] = entity_id
        self._length += 1
        return row

    def remove_entity(self, row_id) -> int:
        """Remove entity from archetype by row

        To keep the array dense - move the last entity to the position of the removed
        entity, unless it was the last entity.

        Args:
            row_id (int): the location of the entity within the archetype storage
        Returns:
            entity_id: the id of the entity that now occupies row_id, or -1 if
                there is none
        """
        if row_id < 0 or row_id >= self._length:
            raise IndexError(f"row_id out of range: {row_id}")

        last_id = self._length - 1
        moved_entity = -1

        if row_id != last_id:
            moved_entity = int(self.entity_ids[last_id])
            for data in self.storage.values():
                data[row_id] = data[last_id]
            self.entity_ids[row_id] = moved_entity
        self.entity_ids[last_id] = -1
        self._length -= 1
        return moved_entity
