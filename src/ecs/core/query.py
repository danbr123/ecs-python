from typing import Optional, Sequence, Type

from .archetype import Archetype
from .component import Component, ComponentRegistry


class Query:
    def __init__(
        self,
        include: list[Type[Component]],
        exclude: Optional[list[Type[Component]]],
        registry: ComponentRegistry,
    ):
        """Stores and fetches archetypes that contain specific components

        The Query object can be used to efficiently fetch all archetype with certain
        components. Each query contains an "include" and "exclude" list that specify
        the desired combination of components. The result archetype must contain all
        components in "include" and none of the components in "exclude".

        The query is performed by matching the signature of the archetype with the bits
        of the required component - so it can be performed very efficiently.

        The query stores the matches for caching, and should be updated when a new
        archetype is introduced by calling `Query.try_add(new_archetype)`.

        The query returns a generator that iterates over all matched archetypes and
        returns the entity_id to row mapping within that archetype, as well as a view
        of the relevant archetype storage.

        Args:
            include: list of components that should be in the matched archetypes
            exclude: list of components that should not be in the matched archetypes
            registry: component registry for signature calculations
        """
        self.include = include
        if exclude is None:
            exclude = []
        self.mask = registry.get_signature(include)
        self.exclude_mask = registry.get_signature(exclude)
        self.matches: list[Archetype] = []

    def try_add(self, arch: Archetype):
        """Attempt to add an archetype to the query

        Match the signature of the archetype with the query masks (bits of desired
        components and excluded components) to see if there is a perfect overlap
        for the include mask and no overlap (or the exclude mask.

        If the archetype matches the query - add it to the matches list.

        If the archetype already exists - do nothing.

        Args:
            arch: archetype to check
        """
        if arch in self.matches:
            return
        if (arch.signature & self.mask) != self.mask:
            return
        if arch.signature & self.exclude_mask:
            return
        self.matches.append(arch)

    def fetch(self, optional: Optional[Sequence[Component]] = None):
        """Fetch the matched archetypes for the query

        If optional components are provided, fetch them as well if the archetype
        has these components.

        Returns:
            a generator that yields tuples:
            - entity_ids: numpy array that matches rows in the archetype to entity ids
              for example: if `entity_ids[3] == 5` - entity 5 occupies row 3 in the
              storage, and that row number can be used to access its data.
            - storage_data: dictionary of {component_type: storage} where the component
              type is one of the archetype's components, and the storage is the array
              that contains that component data.

        Args:
            optional: list of additional component to fetch. by default, only `include`
                components are fetched.
        """
        optional = optional or []
        for arch in self.matches:
            fetch_comps = self.include + [c for c in optional if c in arch.components]
            yield arch.entity_ids[: len(arch)], {
                t: arch.storage[t][: len(arch)] for t in fetch_comps
            }


class QueryManager:

    def __init__(self, component_registry: ComponentRegistry):
        """Creates, stores and updates queries

        The QueryManager can be used to get queries for specific components
        compositions. if such query does not exist - it creates it. If it does exist,
        it returns it from a query storage.

        Args:
            component_registry (ComponentRegistry): registry for signature calculations
        """
        self.registry = component_registry
        self._queries: dict[
            tuple[frozenset[Type[Component]], frozenset[Type[Component]]], Query
        ] = {}

    def on_arch_created(self, arch):
        """Triggers `try_add` on all registered queries

        This function should be called when a new archetype is created.

        Args:
            arch (Archetype): new archetype
        """
        for query in self._queries.values():
            query.try_add(arch)

    def get_query(
        self, include: list[Type[Component]], exclude: Optional[list[Type[Component]]]
    ) -> tuple[Query, bool]:
        """Get a query for a specific component composition

        If the query already exists - return it from the storage.
        If it doesn't  - create it.

        Note:
            The function does not update new queries with all existing archetypes. this
            is the responsibility of the caller. The function returns an "is_new" flag
            to indicate whether the query is new or not.

        Args:
            include: list of components that should be in the matched archetypes
            exclude: list of components that should not be in the matched archetypes

        Returns:
            tuple of:
            - query - the query that matches the required composition (new or existing)
            - is_new - boolean indicating whether the query is new or not - used to
              update the query archetypes after creation.
        """
        key = (frozenset(include), frozenset(exclude or []))
        if key in self._queries:
            return self._queries[key], False
        new_query = Query(include, exclude, self.registry)
        self._queries[key] = new_query
        return new_query, True
