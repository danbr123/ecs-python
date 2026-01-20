# CommandBuffer

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / CommandBuffer

> Auto-generated documentation for [core.command_buffer](../../../src/ecs/core/command_buffer.py) module.

- [CommandBuffer](#commandbuffer)
  - [CommandBuffer](#commandbuffer-1)
    - [CommandBuffer().add_components](#commandbuffer()add_components)
    - [CommandBuffer().clear](#commandbuffer()clear)
    - [CommandBuffer().create_entity](#commandbuffer()create_entity)
    - [CommandBuffer().flush](#commandbuffer()flush)
    - [CommandBuffer().remove_components](#commandbuffer()remove_components)
    - [CommandBuffer().remove_entity](#commandbuffer()remove_entity)

## CommandBuffer

[Show source in command_buffer.py:11](../../../src/ecs/core/command_buffer.py#L11)

#### Signature

```python
class CommandBuffer:
    def __init__(self, world: World): ...
```

### CommandBuffer().add_components

[Show source in command_buffer.py:28](../../../src/ecs/core/command_buffer.py#L28)

Add components to an entity

#### Signature

```python
def add_components(self, entity_id, components_data: dict[Type[Component], Any]): ...
```

### CommandBuffer().clear

[Show source in command_buffer.py:51](../../../src/ecs/core/command_buffer.py#L51)

#### Signature

```python
def clear(self): ...
```

### CommandBuffer().create_entity

[Show source in command_buffer.py:17](../../../src/ecs/core/command_buffer.py#L17)

Create a new entity with initial data

#### Signature

```python
def create_entity(self, components_data: dict[Type[Component], Any]): ...
```

### CommandBuffer().flush

[Show source in command_buffer.py:36](../../../src/ecs/core/command_buffer.py#L36)

#### Signature

```python
def flush(self): ...
```

### CommandBuffer().remove_components

[Show source in command_buffer.py:32](../../../src/ecs/core/command_buffer.py#L32)

Remove components from an entity

#### Signature

```python
def remove_components(self, entity_id, components: list[Type[Component]]): ...
```

### CommandBuffer().remove_entity

[Show source in command_buffer.py:24](../../../src/ecs/core/command_buffer.py#L24)

Remove an entity from the world

#### Signature

```python
def remove_entity(self, entity_id): ...
```