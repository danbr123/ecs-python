# How to use the Query object

## The `Query` object

The `Query` object is the main way to retrieve entities with certain components.
When initialized, the query receives lists of components that should be included or 
excluded from it, and it finds and caches all the archetypes that match that list.
The cache is updated automatically when a new Archetype is introduced.

Since all the matching entities are a part of the cached archetypes, the query can fetch results 
almost instantly, regardless of the number of matched archetypes/entities. The cache update works
with the archetype signature so it is also extremely fast even when the world has a large amount
of archetypes.

Note that each query is represented by the included and excluded lists, and is unique per world. 
Trying to generate a new query with the same arguments will return the existing query.

## How to use

### Initialization

```python
import numpy as np

from ecs.core.world import World
from ecs.core.component import Component, TagComponent


class Planet(TagComponent):
    pass

class Mass(Component):
    dtype = np.float64
    shape = (1,)

class Velocity(Component):
    dtype = np.float64
    shape = (2,)

class Position(Component):
    dtype = np.float64
    shape = (2,)

    
world = World()

# this returns a Query object - it can be used to fetch the results
# multiple times.
my_query = world.query(include=[Position, Velocity], exclude=[Planet])
```

### Getting results - `Query.fetch()`
Once initialized, a query object can be used multiple times to access the cached archetypes 
using `Query.fetch()`. The result is a generator object that can be used to iterate over the
matched `archetypes` their `entities`, and their `data`:

#### archetype
The archetype object of a matched archetype

#### entities
entities is a numpy array of entities and their internal row id within the archetype
since the archetype storage is dense, it is not indexed by the entity id. 
This value can be used to map the row index back to the entity id it represents.

`entities[x]` is the entity id whose data is located in row x.

#### data
Data is a dictionary of {component: array}, it is a view of the archetype storage. it can
be used to read or modify the storage in-place.
Note that data only contains the requested Components (specified in "include") and
only contains populated rows (since the array is dense this means storage[:len(entities)]
to fetch more components - use the `optional` arg in `fetch()`

```python
# fetch all the non-planet entities with a position and velocity
query_result = my_query.fetch()

# query_result is a generator that can be iterated to fetch the results per archetype
for arch, entities, data in query_result:
    # arch is one of the matching archetypes
    comps = arch.components
    assert Position in comps
    assert Planet not in comps
    
    # entities is a numpy array of entities and their internal row id within the arch
    entity_0_row = np.where(entities == 0)[0]
    
    # data is a dictionary of {component: array}, it is a view of the archetype
    # storage.
    positions = data[Position]
    velocities = data[Velocity]
    
    try:
        masses = data[Mass]  # will raise KeyError
    except KeyError:
        pass
    
    # Since this is a view of the real archetype storage and not a copy - we can modify
    # it in-place.
    positions += velocities
    
    # we can also find specific entities in the storage using `entities` from before
    slow_mask = np.sum(velocities, axis=1) < 1
    slow_entities = entities[slow_mask]
```
### Optional components
if we want a component that isn't a part of the query definition - we must request it 
explicitly with `Query.fetch(optional=...)`. this can be done on the same query and doesn't 
require additional lookup or cache update.

Note that the component is NOT guaranteed to exist in every archetype. if it's strictly
required it should be added to Query `include` list.

```python
query_result = my_query.fetch(optional=[Mass])

for arch, entities, data in query_result:
    try:
        mass = data[Mass]  # May throw a KeyError - mass isn't necessarily included
    except KeyError:
        continue

```


### Using `Query.gather()`

The `gather` function can be used to collect all the results of the query into a single
array per component. It is particularly useful when we want to perform the same operation
on all the archetypes, and want to avoid unnecessary loops.

This function works differently from the `fetch` function - as it returns a copy of the 
archetype storage, and for write operations the results must be scattered back to
the archetype storage manually.

The `gather` function returns a `QueryGatherResult` object with the following fields:

- ids - merged array of entity ids from each archetype (merged version of `entities` from `fetch`)
- slices - dictionary of {archetype: slice} - specify the start and end indexes of 
  each archetype in the merged arrays. Can be used to scatter the results later.
- data - similar to `data` in `query.fetch` - dictionary of {component: array} with the merged
  arrays.

#### Example use case
In this example we want to run an N-body gravity simulator. Since entities with mass may
be scattered in many archetypes, and we need to perform the force calculation on every pair
of entities in every archetype (calculation is not "local" inside the archetype storage), we
must first collect all the positions, velocities and masses.


Naive use (`Query.fetch` only):

```python
class GravitySystem(System):
    ...
    
    def update(self, world: World, dt: float) -> None:
        g_const = world.resources.get("G", DEFAULT_G)

        # Since gravity is a "global" interaction and different archetypes affect each
        # other, to perform the operation efficiently we cannot apply the calculations
        # on the archetype storage directly (python and numpy overhead would be
        # significant compared to the smaller arrays).
        # instead - we gather all the data in dense arrays and maintain the original
        # slices indices, perform the operations in one go and then scatter the results
        # back to the archetype storages.
        all_positions = []
        all_masses = []
        arch_slices = {}

        curr_idx = 0

        query_res = list(self.queries["planets"].fetch(optional=[Velocity, Locked]))
        for arch, entities, arch_data in query_res:
            all_positions.append(arch_data[Position])
            all_masses.append(arch_data[Mass])
            added = len(entities)
            arch_slices[arch] = (curr_idx, curr_idx + added)
            curr_idx += added

        if not all_positions:
            return

        positions = np.concatenate(all_positions)
        masses = np.concatenate(all_masses)

        # calculate forces using numba
        acc = calculate_gravity(positions, masses, g_const)

        for arch, entities, arch_data in query_res:
            if Locked not in arch.components and Velocity in arch.components:
                arch_data[Velocity] += acc[arch_slices[arch][0]: arch_slices[arch][1]] * dt
```

With `Query.gather`:
```python
class GravitySystem(System):
    ...

    def update(self, world: World, dt: float) -> None:
        g_const = world.resources.get("G", DEFAULT_G)

        gather_results = self.queries["planets"].gather()
        if len(gather_results.ids) == 0:
            return

        # calculate forces using numba
        acc = calculate_gravity(gather_results[Position], gather_results[Mass], g_const)

        for arch, entities, arch_data in self.queries["planets"].fetch(
            optional=[Velocity, Locked]
        ):
            if (arch in gather_results.slices and Locked not in arch.components 
                and Velocity in arch.components):
                arch_data[Velocity] += acc[gather_results.slices[arch]] * dt

```