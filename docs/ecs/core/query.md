# Query

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / Query

> Auto-generated documentation for [core.query](../../../src/ecs/core/query.py) module.

- [Query](#query)
  - [Query](#query-1)
    - [Query().fetch](#query()fetch)
    - [Query().gather](#query()gather)
    - [Query().try_add](#query()try_add)
  - [QueryGatherResult](#querygatherresult)
  - [QueryManager](#querymanager)
    - [QueryManager().get_query](#querymanager()get_query)
    - [QueryManager().on_arch_created](#querymanager()on_arch_created)

## Query

[Show source in query.py:34](../../../src/ecs/core/query.py#L34)

#### Signature

```python
class Query:
    def __init__(
        self,
        include: list[Type[Component]],
        exclude: Optional[list[Type[Component]]],
        registry: ComponentRegistry,
    ): ...
```

### Query().fetch

[Show source in query.py:92](../../../src/ecs/core/query.py#L92)

Safe way to fetch the matched archetypes for the query

If optional components are provided, fetch them as well if the archetype
has these components.
This function is slightly less efficient than accessing the archetypes directly
via `query.matches`, but it organizes and slices the data automatically,
removing the risk of reading uninitialized garbage data.

#### Notes

For higher efficiency and when using a very large number of archetype, use
`query.matches` to get the archetypes directly, and access their storage
with `archetype.storage`.

#### Arguments

- `optional` - list of additional component to fetch. by default, only `include`
    components are fetched.

#### Yields

(archetype, entity_ids, components):
    - `archetype` - the matched archetype
    - `entity_ids` - numpy array that matches rows in the archetype to entity ids
      - `for` *example* - if `entity_ids[3] == 5` - entity 5 occupies row 3 in the
      storage, and that row number can be used to access its data.
    - `storage_data` - dictionary of {component_type: storage} where the
      component type is one of the archetype's components, and the storage
      is the array that contains that component data.

#### Signature

```python
def fetch(self, optional: Optional[Sequence[Type[Component]]] = None): ...
```

### Query().gather

[Show source in query.py:131](../../../src/ecs/core/query.py#L131)

Gather data from all matched archetypes in a single array per component

IMPORTANT: This function returns a new array and not a view of the archetype
    storage. to apply changes made to the array, use `result["slices"]` to
    determine how to scatter the data back to the original archetypes.

This method can be used when a query returns multiple archetypes but the same
operation needs to be applied to all of them. It is particularly useful when
the calculation depend on data from multiple archetypes - as once the data is
merged any calculation can be done on single arrays.

#### Arguments

- `optional` - list of additional component to fetch. by default, only `include`.
    unlike [Query().fetch](#queryfetch), thif fucntion does not allow optional components
    that are not subclasses of TagComponent, as that creates inconsistent
    data.

#### Returns

dictionary of:
    - `"ids"` - the entity_ids array from each archetype, merged into a single
        array.
    - `"slices"` - dict of {Archetype: slice} where slice can be used to fetch
        the data related to that specific archetype from the merged arrays.
    - `**components_data` - for each component C (include + optional) - the
        value of results[C] is the merged array of all the data of that
        components from all the matched archetypes. For TagComponent - the
        values are boolean flags (1 if the component exists in that
        archetype, 0 if it doesn't)

#### Signature

```python
def gather(
    self, optional: Optional[Sequence[Type[TagComponent]]] = None
) -> QueryGatherResult: ...
```

#### See also

- [QueryGatherResult](#querygatherresult)

### Query().try_add

[Show source in query.py:70](../../../src/ecs/core/query.py#L70)

Attempt to add an archetype to the query

Match the signature of the archetype with the query masks (bits of desired
components and excluded components) to see if there is a perfect overlap
for the include mask and no overlap (or the exclude mask.

If the archetype matches the query - add it to the matches list.

If the archetype already exists - do nothing.

#### Arguments

- `arch` - archetype to check

#### Signature

```python
def try_add(self, arch: Archetype): ...
```



## QueryGatherResult

[Show source in query.py:9](../../../src/ecs/core/query.py#L9)

#### Signature

```python
class QueryGatherResult:
    def __init__(
        self,
        ids: np.ndarray,
        slices: dict["Archetype", slice],
        data: dict[Type[Component], np.ndarray],
    ): ...
```



## QueryManager

[Show source in query.py:208](../../../src/ecs/core/query.py#L208)

#### Signature

```python
class QueryManager:
    def __init__(self, component_registry: ComponentRegistry): ...
```

### QueryManager().get_query

[Show source in query.py:236](../../../src/ecs/core/query.py#L236)

Get a query for a specific component composition

If the query already exists - return it from the storage.
If it doesn't  - create it.

#### Notes

The function does not update new queries with all existing archetypes. this
is the responsibility of the caller. The function returns an "is_new" flag
to indicate whether the query is new or not.

#### Arguments

- `include` - list of components that should be in the matched archetypes
- `exclude` - list of components that should not be in the matched archetypes

#### Returns

tuple of:
- query - the query that matches the required composition (new or existing)
- is_new - boolean indicating whether the query is new or not - used to
  update the query archetypes after creation.

#### Signature

```python
def get_query(
    self, include: list[Type[Component]], exclude: Optional[list[Type[Component]]]
) -> tuple[Query, bool]: ...
```

#### See also

- [Query](#query)

### QueryManager().on_arch_created

[Show source in query.py:225](../../../src/ecs/core/query.py#L225)

Triggers `try_add` on all registered queries

This function should be called when a new archetype is created.

#### Arguments

- `arch` *Archetype* - new archetype

#### Signature

```python
def on_arch_created(self, arch): ...
```