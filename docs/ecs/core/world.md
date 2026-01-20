# World

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / World

> Auto-generated documentation for [core.world](../../../src/ecs/core/world.py) module.

- [World](#world)
  - [World](#world-1)
    - [World().add_components](#world()add_components)
    - [World().create_entity](#world()create_entity)
    - [World().entity_count](#world()entity_count)
    - [World().flush](#world()flush)
    - [World().get_archetype](#world()get_archetype)
    - [World().get_component](#world()get_component)
    - [World().get_system](#world()get_system)
    - [World().query](#world()query)
    - [World().register_system](#world()register_system)
    - [World().remove_components](#world()remove_components)
    - [World().remove_entity](#world()remove_entity)
    - [World().reserve_id](#world()reserve_id)
    - [World().set_component](#world()set_component)
    - [World().update](#world()update)
    - [World().update_systems](#world()update_systems)
    - [World().write_lock](#world()write_lock)

## World

[Show source in world.py:17](../../../src/ecs/core/world.py#L17)

Central coordinator for the ECS runtime.

The World is the composition root for the ECS. It owns the component registry
and wires together the entity, query, resource, and events. Most gameplay or
simulation code should interact with the ECS through this object rather than talking
to managers directly.

Responsibilities:
  - Create and remove entities.
  - Add, remove, get, and set component data on entities.
  - Build and cache queries over archetypes.
  - Systems: register systems and control their update order.
  - Provide an event bus for event dispatch and async events processing.
  - Store global resources shared across systems.

#### Notes

- The World owns a single ComponentRegistry instance. All archetype
  signatures are derived from that registry. DO NOT replace the registry
  after the world has created archetypes/entities, as signatures would no
  longer be comparable.
- This class is currently not thread-safe. Structural changes (creating entities,
  adding/removing components) should be coordinated with iteration if your
  systems perform queries while mutating the world.

#### Attributes

- systems (list[System]): Registered systems, sorted by priority.
- event_bus (EventBus): Event dispatcher and async event queue.
- registry (ComponentRegistry): Assigns component bits used to build archetype
  signatures.
- query_manager (QueryManager): Caches queries and tracks newly created
  archetypes so queries stay up to date.
- entities (EntityManager): Creates entities and manages their lifecycle.
- resources (Resources): Container for global resources.

#### Signature

```python
class World:
    def __init__(self): ...
```

### World().add_components

[Show source in world.py:104](../../../src/ecs/core/world.py#L104)

Add components to an entity

#### Signature

```python
@_lock_on_sys_update
def add_components(self, entity_id, components_data: dict[Type[Component], Any]): ...
```

### World().create_entity

[Show source in world.py:90](../../../src/ecs/core/world.py#L90)

Create a new entity with initial data

#### Signature

```python
@_lock_on_sys_update
def create_entity(
    self, components_data: dict[Type[Component], Any], reserved_id: Optional[int] = None
) -> int: ...
```

### World().entity_count

[Show source in world.py:215](../../../src/ecs/core/world.py#L215)

#### Signature

```python
@property
def entity_count(self) -> int: ...
```

### World().flush

[Show source in world.py:195](../../../src/ecs/core/world.py#L195)

Execute all commands in the command buffer

Apply all structural changes that are buffered in the command buffer (called
by a system but not yet executed).
This happens automatically after each system is updated. this function provides
a way to manually perform this action to make these changes available to the
system immediately.

WARNING: Executing structural commands while iterating over query results may
result in unexpected behavior and corrupted data. Do not use this function
unless you know what you are doing.

#### Signature

```python
def flush(self): ...
```

### World().get_archetype

[Show source in world.py:210](../../../src/ecs/core/world.py#L210)

#### Signature

```python
def get_archetype(self, entity_id: int) -> Archetype: ...
```

### World().get_component

[Show source in world.py:114](../../../src/ecs/core/world.py#L114)

Retrieve an entity component value

#### Signature

```python
def get_component(self, entity_id: int, comp_type: Type[Component]) -> Any: ...
```

### World().get_system

[Show source in world.py:148](../../../src/ecs/core/world.py#L148)

#### Signature

```python
def get_system(self, system_type: Type[_SysType]) -> _SysType: ...
```

### World().query

[Show source in world.py:122](../../../src/ecs/core/world.py#L122)

Query all archetype with a matching composition

If the query is new, update it with all existing archetypes.

#### Arguments

- `include` - list of components that should be in the matched archetypes
- `exclude` - list of components that should not be in the matched archetypes

#### Returns

Query object that can return the relevant Archetypes

#### Signature

```python
def query(
    self, include: list[Type[Component]], exclude: list[Type[Component]] = None
) -> Query: ...
```

### World().register_system

[Show source in world.py:141](../../../src/ecs/core/world.py#L141)

Register a new system

#### Signature

```python
def register_system(self, system: System) -> None: ...
```

### World().remove_components

[Show source in world.py:109](../../../src/ecs/core/world.py#L109)

Remove components from an entity

#### Signature

```python
@_lock_on_sys_update
def remove_components(self, entity_id, components: list[Type[Component]]): ...
```

### World().remove_entity

[Show source in world.py:99](../../../src/ecs/core/world.py#L99)

Remove an entity from the world

#### Signature

```python
@_lock_on_sys_update
def remove_entity(self, entity_id): ...
```

### World().reserve_id

[Show source in world.py:87](../../../src/ecs/core/world.py#L87)

#### Signature

```python
def reserve_id(self): ...
```

### World().set_component

[Show source in world.py:118](../../../src/ecs/core/world.py#L118)

Set component value for an entity

#### Signature

```python
def set_component(self, entity_id: int, comp_type: Type[Component], value: Any): ...
```

### World().update

[Show source in world.py:177](../../../src/ecs/core/world.py#L177)

Update the world

Calls the update() method of each registered system and of the event bus.
If a system is disabled - skip the update.
Optionally - choose a specific group of systems and only update them

#### Arguments

- `dt` *float* - time since last system update
- `group` *Optional[str]* - name of the groups to update. only systems with
    `system.group == group` will be updated.
    If None - update all systems.

#### Signature

```python
def update(self, dt: float, group: Optional[str] = None) -> None: ...
```

### World().update_systems

[Show source in world.py:154](../../../src/ecs/core/world.py#L154)

Update the systems in the world

Calls the update() method of each registered system.
If a system is disabled - skip the update.
Optionally - choose a specific group of systems and only update them

#### Arguments

- `dt` *float* - time since last system update
- `group` *Optional[str]* - name of the groups to update. only systems with
    `system.group == group` will be updated.
    If None - update all systems.

#### Signature

```python
def update_systems(self, dt: float, group: Optional[str] = None) -> None: ...
```

### World().write_lock

[Show source in world.py:66](../../../src/ecs/core/world.py#L66)

#### Signature

```python
@contextmanager
def write_lock(self): ...
```