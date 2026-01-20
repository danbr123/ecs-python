# EntityManager

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / EntityManager

> Auto-generated documentation for [core.entity_manager](../../../src/ecs/core/entity_manager.py) module.

- [EntityManager](#entitymanager)
  - [EntityManager](#entitymanager-1)
    - [EntityManager()._assign_id](#entitymanager()_assign_id)
    - [EntityManager()._remove_and_swap](#entitymanager()_remove_and_swap)
    - [EntityManager()._validate_data](#entitymanager()_validate_data)
    - [EntityManager().add](#entitymanager()add)
    - [EntityManager().add_components](#entitymanager()add_components)
    - [EntityManager().deregister_reserved_ids](#entitymanager()deregister_reserved_ids)
    - [EntityManager().get_archetype](#entitymanager()get_archetype)
    - [EntityManager().get_component](#entitymanager()get_component)
    - [EntityManager().remove](#entitymanager()remove)
    - [EntityManager().remove_components](#entitymanager()remove_components)
    - [EntityManager().reserve_id](#entitymanager()reserve_id)
    - [EntityManager().set_component](#entitymanager()set_component)
  - [PendingEntityException](#pendingentityexception)

## EntityManager

[Show source in entity_manager.py:13](../../../src/ecs/core/entity_manager.py#L13)

#### Signature

```python
class EntityManager:
    def __init__(
        self,
        component_registry: ComponentRegistry,
        on_arch_created: Callable[[Archetype], Any],
    ): ...
```

### EntityManager()._assign_id

[Show source in entity_manager.py:77](../../../src/ecs/core/entity_manager.py#L77)

Assign unique entity id

#### Signature

```python
def _assign_id(self): ...
```

### EntityManager()._remove_and_swap

[Show source in entity_manager.py:83](../../../src/ecs/core/entity_manager.py#L83)

Remove entity from archetype by row

After the removal, the archetype fills the empty row with
a different entity id to maintain density, so the function
also updates the row in the entities_map.

#### Arguments

- `arch` *Archetype* - the archetype to remove the entity from
- `row` *int* - the *row* of the entity to remove from the archetype

#### Signature

```python
def _remove_and_swap(self, arch: Archetype, row: int): ...
```

### EntityManager()._validate_data

[Show source in entity_manager.py:59](../../../src/ecs/core/entity_manager.py#L59)

Perform validation of data against component schema.

#### Signature

```python
def _validate_data(self, comp_type: Type[Component], value: Any): ...
```

### EntityManager().add

[Show source in entity_manager.py:128](../../../src/ecs/core/entity_manager.py#L128)

Create a new entity with given components

Calculate the matching archetype for the entity based on the components
composition, then insert the entity and its component data to the
archetype storage.
For tag components only the keys in component_data are used, and the values
are ignored.

#### Signature

```python
def add(
    self, components_data: dict[Type[Component], Any], reserved_id: Optional[int] = None
) -> int: ...
```

### EntityManager().add_components

[Show source in entity_manager.py:180](../../../src/ecs/core/entity_manager.py#L180)

Add a components to an existing entity

Calculate the new archetype for the entity based on the new components
composition, then:
- Add the entity to the new archetype
- Copy existing entity data from the previous archetype to the new one
- Remove the entity from the old archetype
- add the new component data to the new archetype

If all components already exist (archetype doesn't change) - this function
behaves similarly to multiple calls of [EntityManager().set_component](#entitymanagerset_component)

if the entity doesn't exist - raise an exception.

#### Notes

- `IMPORTANT` - Since moving entities between archetypes is relatively
inefficient, it is recommended to add all new components in a single call
when possible.
in general, if a component is expected to be added/removed frequently, it
is recommended to use a flag component that enables/disables it instead
of actively removing it.

#### Arguments

- `entity_id` *int* - the entity to add the new components to
components_data (dict[Type[Component], Any]): dictionary of {type: data}
    where data is a numpy array or scalar with a shape matching the
    component schema.
    for TagComponents, the value is ignored.

#### Signature

```python
def add_components(
    self, entity_id: int, components_data: dict[Type[Component], Any]
): ...
```

### EntityManager().deregister_reserved_ids

[Show source in entity_manager.py:122](../../../src/ecs/core/entity_manager.py#L122)

#### Signature

```python
def deregister_reserved_ids(self, ids: list[int]): ...
```

### EntityManager().get_archetype

[Show source in entity_manager.py:98](../../../src/ecs/core/entity_manager.py#L98)

Get archetype for a given component composition

If an archetype does not exist yet, create it.
Use the archetype signature for efficient lookup.

#### Arguments

- `components` *list[Type[Component]]* - list of components

#### Returns

- `archetype` *Archetype* - an archetype that matches the component composition

#### Signature

```python
def get_archetype(self, components: list[Type[Component]]) -> Archetype: ...
```

### EntityManager().get_component

[Show source in entity_manager.py:286](../../../src/ecs/core/entity_manager.py#L286)

Get the value of a specific component of an entity

if the entity doesn't exist - raise an exception.

#### Arguments

- `entity_id` *int* - the entity to get the component value for
- `comp_type` *Type[Component]* - the type of component to get

#### Returns

- `value` - a scalar or numpy array with the component value

#### Raises

- `ValueError` - if the entity doesn't exist or doesn't have the component
- [PendingEntityException](#pendingentityexception) - if the entity is pending

#### Signature

```python
def get_component(self, entity_id: int, comp_type: Type[Component]) -> Any: ...
```

### EntityManager().remove

[Show source in entity_manager.py:161](../../../src/ecs/core/entity_manager.py#L161)

Remove an entity

Remove the entity from its archetype and from the entities_map.
if the entity doesn't exist - raise an exception.

#### Arguments

- `entity_id` *int* - the entity to remove

#### Returns

- `entity_id` *int* - the removed entity

#### Signature

```python
def remove(self, entity_id: int) -> int: ...
```

### EntityManager().remove_components

[Show source in entity_manager.py:249](../../../src/ecs/core/entity_manager.py#L249)

Remove components from an existing entity

Remove components from an entity by deleting it from its archetype
and adding it to a new archetype that matches the new component composition.

if the entity doesn't exist - raise an exception.

#### Notes

this operation changes the archetype and copies the entity data and
is therefore relatively inefficient. see docstring in
[EntityManager().add_components](#entitymanageradd_components) for more information and best practices.

#### Signature

```python
def remove_components(self, entity_id: int, components: list[Type[Component]]): ...
```

### EntityManager().reserve_id

[Show source in entity_manager.py:116](../../../src/ecs/core/entity_manager.py#L116)

Reserve an id for an entity without creating it

#### Signature

```python
def reserve_id(self): ...
```

### EntityManager().set_component

[Show source in entity_manager.py:317](../../../src/ecs/core/entity_manager.py#L317)

Set the value for a specific component of an entity

New value must match the component schema.
if the entity doesn't exist - raise an exception.

#### Notes

it is not recommended to use this function to add components to an entity,
use [EntityManager().add_components](#entitymanageradd_components) instead.

#### Arguments

- `entity_id` *int* - the entity to set the component value for
- `comp_type` *Type[Component]* - the type of component to set
- `value` *Any* - a scalar or numpy array with the component value

#### Raises

- `ValueError` - if the entity doesn't exist or doesn't have the component
- [PendingEntityException](#pendingentityexception) - if the entity is pending

#### Signature

```python
def set_component(self, entity_id: int, comp_type: Type[Component], value: Any): ...
```



## PendingEntityException

[Show source in entity_manager.py:9](../../../src/ecs/core/entity_manager.py#L9)

#### Signature

```python
class PendingEntityException(Exception): ...
```