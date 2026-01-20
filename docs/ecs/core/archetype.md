# Archetype

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / Archetype

> Auto-generated documentation for [core.archetype](../../../src/ecs/core/archetype.py) module.

- [Archetype](#archetype)
  - [Archetype](#archetype-1)
    - [Archetype().allocate](#archetype()allocate)
    - [Archetype().increase_capacity](#archetype()increase_capacity)
    - [Archetype().remove_entity](#archetype()remove_entity)

## Archetype

[Show source in archetype.py:8](../../../src/ecs/core/archetype.py#L8)

#### Signature

```python
class Archetype:
    def __init__(
        self,
        components: list[Type[Component]],
        signature: int,
        initial_capacity: int = 256,
    ): ...
```

### Archetype().allocate

[Show source in archetype.py:68](../../../src/ecs/core/archetype.py#L68)

Add a new entity to the archetype

Add the entity to the mapping and allocate a row.
This function DOES NOT insert entity data, this is performed by the
EntityManager.
The function returns the row of the entity id within the archetype storage.
This row is used by the EntityManager to locate the entity inside the Archetype.

#### Arguments

- `entity_id` *int* - entity_id to add

#### Returns

- `row` *int* - the row of the entity id

#### Signature

```python
def allocate(self, entity_id: int) -> int: ...
```

### Archetype().increase_capacity

[Show source in archetype.py:55](../../../src/ecs/core/archetype.py#L55)

Double the capacity of the archetype arrays

#### Signature

```python
def increase_capacity(self): ...
```

### Archetype().remove_entity

[Show source in archetype.py:89](../../../src/ecs/core/archetype.py#L89)

Remove entity from archetype by row

To keep the array dense - move the last entity to the position of the removed
entity, unless it was the last entity.

#### Arguments

- `row_id` *int* - the location of the entity within the archetype storage

#### Returns

- `entity_id` - the id of the entity that now occupies row_id, or -1 if
    there is none

#### Signature

```python
def remove_entity(self, row_id) -> int: ...
```