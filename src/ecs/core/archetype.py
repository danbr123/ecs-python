from typing import Type

import numpy as np

from .component import Component


class Archetype:
    def __init__(self, components: list[Type[Component]], signature: int, initial_capacity: int = 256):
        self.signature = signature
        self.components = components
        self._capacity = initial_capacity
        self.storage: dict[Type[Component], np.ndarray] = {
            c: np.zeros((self._capacity, *c.shape), dtype=c.dtype)
            for c in components
        }
        self.entity_ids = np.full(self._capacity, -1, dtype=np.int32)
        self._length = 0

    def __len__(self):
        return self._length

    def increase_capacity(self):
        new_capacity = self._capacity * 2
        new_entities = np.full(new_capacity, -1, dtype=np.int32)
        new_entities[:self._capacity] = self.entity_ids[:self._capacity]
        self.entity_ids = new_entities

        for comp, data in self.storage.items():
            _new_data = np.zeros((new_capacity, *data.shape[1:]), dtype=data.dtype)
            _new_data[:self._capacity] = data[:self._capacity]
            self.storage[comp] = _new_data
        self._capacity = new_capacity

    def allocate(self, entity_id: int) -> int:
        if self._length >= self._capacity:
            self.increase_capacity()
        row = self._length
        self.entity_ids[row] = entity_id
        self._length += 1
        return row

    def remove_entity(self, row_id):
        """Remove entity from archetype by row

        To keep the array dense - move the last entity to the position of
        the removed entity, unless it was the last entity.

        Args:
            row_id: the location of the entity within the archetype storage
        Returns:
            the entity_id of the entity that now occupies row_id, or -1 if there is none
        """
        last_id = self._length - 1
        moved_entity = -1

        if row_id != last_id:
            moved_entity = self.entity_ids[last_id]
            for data in self.storage.values():
                data[row_id] = data[last_id]
            self.entity_ids[row_id] = moved_entity
        self.entity_ids[last_id] = -1
        self._length -= 1
        return moved_entity

