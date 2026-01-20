# ecs-python - Getting started

This guide shows how to get started with the ECS package, as well as some of the basic functionalites.
The examples are based on the gravity simulator example in `examples/gravity_sim.py`.

### define components
Components are simple data containers. They are the building blocks that can be used to create
entities and attach data to them.
Using components (composition) instead of inheritance allows significantly more flexibility than standard OOP.

```python
import numpy as np

from ecs import Component, TagComponent

class Mass(Component):
    dtype = np.float64
    shape = (1,)

class Velocity(Component):
    dtype = np.float64
    shape = (2,)

class Position(Component):
    dtype = np.float64
    shape = (2,)

class Radius(Component):
    dtype = np.float64
    shape = (1,)

# TagComponents are used for tags or flags that rarely change. they do not
# store any data but affect the entity archetype.
class Planet(TagComponent):
    pass

class Star(TagComponent):
    pass

class Locked(TagComponent):
    # lock entity in place
    pass

```

### Create your systems (game logic)
Systems contain the logic. They query for entities with specific components and modify their data.


```python
import numpy as np

from ecs import System, World
from somewhere import calculate_gravity


class MovementSystem(System):
    group = "physics"

    def initialize(self, world: World) -> None:
        self.queries["planets"] = world.query(
            include=[Mass, Position, Velocity], exclude=[Locked]
        )

    def update(self, world: World, dt: float) -> None:
        for _, _, data in self.queries["planets"].fetch():
            data[Position] += data[Velocity] * dt


class AccelerationSystem(System):
    group = "physics"  # this system will be updated with other "physics" systems

    def initialize(self, world: World) -> None:
        self.queries["planets"] = world.query(include=[Mass, Position])

    def update(self, world: World, dt: float) -> None:
        g_const = world.resources.get("G", 0.667)  # get shared configuration from world object

        gather_res = self.queries["planets"].gather()
        if len(gather_res.ids) == 0:
            return

        acc = calculate_gravity(gather_res[Position], gather_res[Mass], g_const)

        for arch, entities, arch_data in self.queries["planets"].fetch(
            optional=[Velocity, Locked]
        ):
            if (
                arch in gather_res.slices
                and Locked not in arch.components
                and Velocity in arch.components
            ):
                arch_data[Velocity] += acc[gather_res.slices[arch]] * dt

class RenderSystem(System):
    group = "render"
    def update(self, world: World, dt: float) -> None: ...
```

### Create your world
The World acts as the container for all entities and systems.

```python
from ecs import World

world = World()
world.register_system(AccelerationSystem(priority=1))
world.register_system(MovementSystem(priority=2))  # runs after gravity calculation
world.register_system(RenderSystem(priority=100))  # runs last\

# attach shared resources
world.resources["G"] = 0.667  # can be accessed by all systems
```

### Add entities to your world

```python

star_components = {
    Position: (0, 0),
    Velocity: (0, 0),
    Mass: 1000,
    Star: None  # value doesn't matter for TagComponents
}


planet_components = {
    Position: (100, 100),
    Velocity: (200, 0),
    Mass: 100,
    Planet: None
}

world.create_entity(star_components)
world.create_entity(planet_components)
```

### Run your game
Call `world.update()` inside your main loop. 

You can update specific system groups at different frequencies.

```python
dt = 1
while True:
    for _ in range(10):
        # physics updates run x10 more frequently than rendering
        world.update(dt, group="physics")
    world.update(dt, group="render")
```

### Use Events 
Use the EventBus inside the `World` object for decoupled communication.


```python
from dataclasses import dataclass
from ecs.core.event import Event

@dataclass
class PlanetCreatedEvent(Event):
    position: tuple[float, float]

def event_subscriber(event: PlanetCreatedEvent):
    print(f"Planet created at {event.position}")

world.event_bus.subscribe(PlanetCreatedEvent, event_subscriber)

world.create_entity(planet_components)
world.event_bus.publish_sync(PlanetCreatedEvent(planet_components[Position]))
# >>> Planet created at {event.position}

# If called inside a system - we can use publish_async to make sure the event
# is processed only after the world update is complete.
world.event_bus.publish_async(PlanetCreatedEvent(planet_components[Position]))
# >>> Planet created at {event.position}

```

### Use Command buffer to maintain data integrity during iterations
**IMPORTANT** - you cannot make structural changes to entities (add/remove/change archetype) directly 
inside a system update. This may invalidate the query iterator and can cause crashes or corrupt data.

Instead - use `world.cmd_buffer` to Queue the structural changes and apply them only
after the systems update, when it is safe to do so.

**Bad:**
```python
from ecs import System, World
class MySystem(System):
    
    def initialize(self, world: World) -> None:
        self.my_query = world.query(include=[Position, Velocity])
    
    def update(self, world: World, dt: float):
        for arch, entities, data in self.my_query.fetch():
            ...
            world.create_entity({Position: (0, 0), Velocity: (0, 0)})
            # OOPS - archetype changed during iterations.
            # the line above will cause a RuntimeError to avoid data corruption

```

**Good:**
```python
from ecs import System, World

class MySystem(System):
    
    def initialize(self, world: World) -> None:
        self.my_query = world.query(include=[Position, Velocity])
    
    def update(self, world: World, dt: float):
        for arch, entities, data in self.my_query.fetch():
            ...
            world.cmd_buffer.create_entity({Position: (0, 0), Velocity: (0, 0)})
            # Now the entity will only be created once the system update has been completed.
            # our data is safe!

```

Still want to apply changes during system updates? Use `world.flush()` to apply all
the changes in the buffer (use at your own risk):
```python
from ecs import System, World

class MySystem(System):
    
    def initialize(self, world: World) -> None:
        self.my_query = world.query(include=[Position, Velocity])
    
    def update(self, world: World, dt: float):
        for arch, entities, data in self.my_query.fetch():
            ...
            world.cmd_buffer.create_entity({Position: (0, 0), Velocity: (0, 0)})
        
        # flush to continue working with the updated data
        # SAFETY NOTE: Only flush AFTER the loop is finished, never inside it!
        world.flush()
        for arch, entities, data in self.my_query.fetch():
            # data is now updated with the new entity
            ...

        

```