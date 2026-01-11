from abc import ABC
from typing import Type

import numpy as np


class Component(ABC):
    """Abstract class for an ECS component

    All components must inherit from this class. Optionally, a component
    may also define a schema (shape and dtype).

    An ECS component is a property of an entity. An entity may have multiple
    components associated with it, and these may change over its lifetime.

    Component data may be multidimensional.
    The default value is a scalar (shape= (1,))

    Examples:
        >>> class PositionComponent(Component):
        >>>     shape = (2,)  # (x, y)
        >>>     dtype = np.float32

        >>> class HealthComponent(Component):
        >>>     shape = (1,)
        >>>     dtype = np.int32
    """

    shape: tuple = (1,)
    dtype: np.dtype = np.float32


class ComponentRegistry:

    def __init__(self):
        """Assign unique bits to components and generate signatures"""
        self._component_bits: dict[Type[Component], int] = {}
        self._next_bit = 1
        self._cache: dict[frozenset[Type[Component]], int] = {}

    def get_bit(self, comp_type):
        """Get component bit, assign one if it doesn't have one"""
        if comp_type not in self._component_bits:
            self._component_bits[comp_type] = self._next_bit
            self._next_bit <<= 1
        return self._component_bits[comp_type]

    def get_signature(self, components: list[Type[Component]]) -> int:
        """Get unique signature for a composition of components.

        The signature is only relevant for a specific registry. Each may have a
        different signature for the same components list.

        Args:
            components: list of component types

        Returns:
            an integer that represents the signature of this component composition.
            Each component affects a unique bit in that signature.
        """
        components = self.sort_components(components)
        cache_key = frozenset(components)
        if cache_key in self._cache:
            return self._cache[cache_key]
        signature = 0
        for comp_type in components:
            signature |= self.get_bit(comp_type)

        self._cache[cache_key] = signature
        return signature

    def sort_components(
        self, components: list[Type[Component]]
    ) -> list[Type[Component]]:
        """Sort components according ton their associated bit and de-duplicate"""
        components = set(components)
        return sorted(components, key=lambda x: self.get_bit(x))
