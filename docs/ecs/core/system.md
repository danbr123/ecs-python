# System

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / System

> Auto-generated documentation for [core.system](../../../src/ecs/core/system.py) module.

- [System](#system)
  - [System](#system-1)
    - [System().disable](#system()disable)
    - [System().enable](#system()enable)
    - [System().initialize](#system()initialize)
    - [System().on_error](#system()on_error)
    - [System().shutdown](#system()shutdown)
    - [System().toggle](#system()toggle)
    - [System().update](#system()update)

## System

[Show source in system.py:11](../../../src/ecs/core/system.py#L11)

#### Attributes

- `group`: `str` - system group that the system belongs to (i.e. render, physics).
  the World.update() function can update systems of specific groups.: 'default'


Abstract base class for systems in the ECS framework.

#### Signature

```python
class System(ABC):
    def __init__(
        self, priority: float = 10.0, enabled: bool = True, name: Optional[str] = None
    ) -> None: ...
```

### System().disable

[Show source in system.py:68](../../../src/ecs/core/system.py#L68)

#### Signature

```python
def disable(self): ...
```

### System().enable

[Show source in system.py:65](../../../src/ecs/core/system.py#L65)

#### Signature

```python
def enable(self): ...
```

### System().initialize

[Show source in system.py:36](../../../src/ecs/core/system.py#L36)

Optional hook called when the system is added to the world.
Use this for one-time setup (queries, resource allocation, caching, etc.).

Note: `System.queries` can be used to cache queries for better performance.
However, doing so will bound the system into a single world (as queries are
bound to a World).
To re-use the system - create a new instance, clear the query cache, or make
sure the same queries are not used in separate worlds.

#### Signature

```python
def initialize(self, world: World) -> None: ...
```

### System().on_error

[Show source in system.py:74](../../../src/ecs/core/system.py#L74)

#### Signature

```python
def on_error(self, world: World, ex: Exception) -> None: ...
```

### System().shutdown

[Show source in system.py:57](../../../src/ecs/core/system.py#L57)

Optional hook called when the system is removed from the world,
or when the world is shutting down.
Use this to clean up resources.

#### Signature

```python
def shutdown(self, world: World) -> None: ...
```

### System().toggle

[Show source in system.py:71](../../../src/ecs/core/system.py#L71)

#### Signature

```python
def toggle(self): ...
```

### System().update

[Show source in system.py:49](../../../src/ecs/core/system.py#L49)

Called every frame/tick if the system is enabled.
Implement your system logic here.

#### Signature

```python
@abstractmethod
def update(self, world: World, dt: float) -> None: ...
```