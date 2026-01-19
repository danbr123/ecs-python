from typing import Optional, Sequence, Type

import numpy as np

from .archetype import Archetype
from .component import Component, ComponentRegistry, TagComponent


class QueryGatherResult:
    __slots__ = ("ids", "slices", "data")

    def __init__(
        self,
        ids: np.ndarray,
        slices: dict["Archetype", slice],
        data: dict[Type[Component], np.ndarray],
    ):
        self.ids = ids
        self.slices = slices
        self.data = data

    def __getitem__(self, component_type: Type[Component]) -> np.ndarray:
        return self.data[component_type]

    def __repr__(self) -> str:
        return (
            f"<GatherResult components={list(self.data.keys())}, count={len(self.ids)}>"
        )

    def __contains__(self, component_type: Type[Component]) -> bool:
        return component_type in self.data


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

    def fetch(self, optional: Optional[Sequence[Type[Component]]] = None):
        """Safe way to fetch the matched archetypes for the query

        If optional components are provided, fetch them as well if the archetype
        has these components.
        This function is slightly less efficient than accessing the archetypes directly
        via `query.matches`, but it organizes and slices the data automatically,
        removing the risk of reading uninitialized garbage data.

        Note:
            For higher efficiency and when using a very large number of archetype, use
            `query.matches` to get the archetypes directly, and access their storage
            with `archetype.storage`.

        Args:
            optional: list of additional component to fetch. by default, only `include`
                components are fetched.

        Yields:
            (archetype, entity_ids, components):
                archetype: the matched archetype
                entity_ids: numpy array that matches rows in the archetype to entity ids
                  for example: if `entity_ids[3] == 5` - entity 5 occupies row 3 in the
                  storage, and that row number can be used to access its data.
                storage_data: dictionary of {component_type: storage} where the
                  component type is one of the archetype's components, and the storage
                  is the array that contains that component data.
        """
        optional = optional or []
        for arch in self.matches:
            fetch_comps = [
                c
                for c in (*self.include, *optional)
                if c in arch.components and not issubclass(c, TagComponent)
            ]
            yield arch, arch.entity_ids[: len(arch)], {
                t: arch.storage[t][: len(arch)] for t in fetch_comps
            }

    def gather(
        self, optional: Optional[Sequence[Type[TagComponent]]] = None
    ) -> QueryGatherResult:
        """Gather data from all matched archetypes in a single array per component

        IMPORTANT: This function returns a new array and not a view of the archetype
            storage. to apply changes made to the array, use `result["slices"]` to
            determine how to scatter the data back to the original archetypes.

        This method can be used when a query returns multiple archetypes but the same
        operation needs to be applied to all of them. It is particularly useful when
        the calculation depend on data from multiple archetypes - as once the data is
        merged any calculation can be done on single arrays.

        Args:
            optional: list of additional component to fetch. by default, only `include`.
                unlike `Query.fetch`, thif fucntion does not allow optional components
                that are not subclasses of TagComponent, as that creates inconsistent
                data.

        Returns:
            dictionary of:
                "ids": the entity_ids array from each archetype, merged into a single
                    array.
                "slices": dict of {Archetype: slice} where slice can be used to fetch
                    the data related to that specific archetype from the merged arrays.
                **components_data: for each component C (include + optional) - the
                    value of results[C] is the merged array of all the data of that
                    components from all the matched archetypes. For TagComponent - the
                    values are boolean flags (1 if the component exists in that
                    archetype, 0 if it doesn't)
        """
        optional = optional or []
        for comp in optional:
            if not issubclass(comp, TagComponent):
                raise ValueError(
                    f"Only subclasses of TagComponent are allowed as optional "
                    f"components when using `Query.gather`, got {type(comp)}"
                )
        total_count = sum(len(arch) for arch in self.matches)

        out_ids = np.empty(total_count, dtype=np.int32)

        data_arrays = {}

        for comp in self.include:
            if issubclass(comp, TagComponent):
                arr = np.ones(total_count, dtype=np.bool_)
            else:
                arr = np.empty(shape=((total_count,) + comp.shape), dtype=comp.dtype)
            data_arrays[comp] = arr
        for comp in optional:
            arr = np.zeros(total_count, dtype=np.bool_)
            data_arrays[comp] = arr

        slices: dict[Archetype, slice] = {}

        if total_count > 0:
            idx = 0
            for arch in self.matches:
                arch_count = len(arch)
                if arch_count == 0:
                    continue
                end = idx + arch_count
                curr_slice = slice(idx, end)
                slices[arch] = curr_slice

                out_ids[curr_slice] = arch.entity_ids[:arch_count]
                for comp in self.include:
                    if not issubclass(comp, TagComponent):
                        data_arrays[comp][curr_slice] = arch.storage[comp][:arch_count]
                for comp in optional:
                    data_arrays[comp][curr_slice] = comp in arch.components
                idx = end
        return QueryGatherResult(ids=out_ids, slices=slices, data=data_arrays)


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
