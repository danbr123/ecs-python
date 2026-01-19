![CI Status](https://github.com/danbr123/ecs-python/actions/workflows/ci.yml/badge.svg)
# ecs-python
ECS framework for python, built to support efficient vectorized operations on entity components.


## introduction
Do you like **video games**?

Do you like **coding**?

Do you think **Python** is the **superior language** but was disappointed to learn that there is
no proper framework for writing high-performance games and simulations in python?

**Well, then go learn C++, because python is not for writing games**.

But until you do that, you can use this package to scratch that itch. python-ecs is a 
Data-Oriented ECS framework designed to squeeze every ounce of performance out of Python 
using NumPy and modern memory layouts. It won't beat C++, but it will make your Python 
games crawl just a bit more quickly.


## What is ECS
Entity Component System (ECS) is a design pattern often used in games and simulations.
Unlike inheritance, which is more intuitive but can be inefficient and has various problems,
this pattern separates the data (Components) from objects (Entities) and logic (Systems),
which allows optimizations such as batch operations, keeping relevant data closer in memory, etc.

## The main components of ECS:

### Entities
Entities are a simple identifier which is used to lookup data in specific components.

### Components
Components are the owners of the data, they define the schema and contain the arrays that
store the data (Note: in this framework we use an Archetype system, which stores the data
instead of the components. see more info below.)

### Systems
Systems define the logic of the game/simulator. They read the state of the game from the 
components and modify it.
Systems should generally be stateless.

### World
The world object manages systems, entities, and all other ECS-related objects.
Most gameplay or simulation code should interact with the ECS through this object.

## Additional objects in this framework

### Archetype
An archetype is a composition of components. it allows us to group entities with an 
identical composition for significantly faster querying and easier management.
An archetype contains a storage of component data (numpy arrays) and a unique bitmask
signature based on the composition, which can be used for querying.

### Query
A query caches and returns all the archetype that match some component composition. the
query can define components that must be in the target archetype and components that must
be excluded from it, and can be used to return all the desired components from all the 
archetypes that match that requirement.
Each composition has a unique query, which caches the results and updates automatically
for high efficiency.

### CommandBuffer
Since adding/removing entities or changing their archetype ("mutations") while looping over query results
could cause problems, all mutations are not executed immediately and are instead buffered
and only executed when the system update is completed.
While changes are buffered they may not be accessible to the system (i.e. an added entity
cannot be accessed until the next update).

### Event and EventBus
These can be used to store and dispatch events. The bus supports synchronous and asynchronous
events dispatch. 
Synchronous events are dispatched immediately upon publication.
Asynchronous events are queued and processed in the next update cycle (frame).

### Resources
Dict wrapper that support type casting, namespaces and more. Can be used to store the world
state, and systems can access it during update. 

## Example usage
```python
import numpy as np
from src.ecs import System, Component, World


class PositionComponent(Component):
    shape = (2,)  # x, y
    dtype = np.float32


class VelocityComponent(Component):
    shape = (2,)  # vx, vy


class MovementSystem(System):

    def initialize(self, world):
        self.query = world.query(include=[PositionComponent, VelocityComponent])

    def update(self, world, dt):
        for _, arch_data in self.query.fetch():
            positions = arch_data[PositionComponent]
            velocities = arch_data[VelocityComponent]
            positions += dt * velocities


world = World()
world.register_system(MovementSystem())
eid = world.create_entity(components_data={
     # for 1d array, conversion to ndarray happens automatically assuming shape and dtypes match
    PositionComponent: (0, 0),
    VelocityComponent: np.array((1, 2), dtype=np.float32)
})
world.update(dt=1)
world.update(dt=1)
print(world.get_component(eid, PositionComponent))  # [2. 4.]
```