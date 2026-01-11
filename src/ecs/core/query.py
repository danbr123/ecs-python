from typing import Optional, Type

from .archetype import Archetype
from .component import Component, ComponentRegistry


class Query:
    def __init__(
        self,
        include: list[Type[Component]],
        exclude: Optional[list[Type[Component]]],
        registry: ComponentRegistry,
    ):
        self.include = include
        if exclude is None:
            exclude = []
        self.mask = registry.get_signature(include)
        self.exclude_mask = registry.get_signature(exclude)
        self.matches: list[Archetype] = []

    def try_add(self, arch: Archetype):
        if arch in self.matches:
            return
        if (arch.signature & self.mask) != self.mask:
            return
        if arch.signature & self.exclude_mask:
            return
        self.matches.append(arch)

    def fetch(self):
        for arch in self.matches:
            yield arch.entity_ids[:len(arch)], {t: arch.storage[t][: len(arch)] for t in self.include}


class QueryManager:

    def __init__(self, component_registry: ComponentRegistry):
        self.registry = component_registry
        self._queries: dict[
            tuple[frozenset[Type[Component]], frozenset[Type[Component]]], Query
        ] = {}

    def on_arch_created(self, arch):
        for query in self._queries.values():
            query.try_add(arch)

    def get_query(
        self, include: list[Type[Component]], exclude: Optional[list[Type[Component]]]
    ) -> tuple[Query, bool]:
        key = (frozenset(include), frozenset(exclude or []))
        if key in self._queries:
            return self._queries[key], False
        new_query = Query(include, exclude, self.registry)
        self._queries[key] = new_query
        return new_query, True
