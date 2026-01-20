# Component

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / Component

> Auto-generated documentation for [core.component](../../../src/ecs/core/component.py) module.

- [Component](#component)
  - [Component](#component-1)
  - [ComponentRegistry](#componentregistry)
    - [ComponentRegistry().get_bit](#componentregistry()get_bit)
    - [ComponentRegistry().get_signature](#componentregistry()get_signature)
    - [ComponentRegistry().sort_components](#componentregistry()sort_components)
  - [TagComponent](#tagcomponent)

## Component

[Show source in component.py:7](../../../src/ecs/core/component.py#L7)

Abstract class for an ECS component

All components must inherit from this class. Optionally, a component
may also define a schema (shape and dtype).

An ECS component is a property of an entity. An entity may have multiple
components associated with it, and these may change over its lifetime.

Component data may be multidimensional.
The default value is a scalar (shape= (1,))

#### Examples

```python
>>> class PositionComponent(Component):
>>>     shape = (2,)  # (x, y)
>>>     dtype = np.float32
```

```python
>>> class HealthComponent(Component):
>>>     shape = (1,)
>>>     dtype = np.int32
```

#### Signature

```python
class Component(ABC): ...
```



## ComponentRegistry

[Show source in component.py:58](../../../src/ecs/core/component.py#L58)

#### Signature

```python
class ComponentRegistry:
    def __init__(self): ...
```

### ComponentRegistry().get_bit

[Show source in component.py:66](../../../src/ecs/core/component.py#L66)

Get component bit, assign one if it doesn't have one

#### Signature

```python
def get_bit(self, comp_type: Type[Component]) -> int: ...
```

#### See also

- [Component](#component)

### ComponentRegistry().get_signature

[Show source in component.py:77](../../../src/ecs/core/component.py#L77)

Get unique signature for a composition of components.

The signature is only relevant for a specific registry. Each may have a
different signature for the same components list.

#### Arguments

- `components` - list of component types

#### Returns

an integer that represents the signature of this component composition.
Each component affects a unique bit in that signature.

#### Signature

```python
def get_signature(self, components: list[Type[Component]]) -> int: ...
```

#### See also

- [Component](#component)

### ComponentRegistry().sort_components

[Show source in component.py:101](../../../src/ecs/core/component.py#L101)

Sort components according to their associated bit and de-duplicate

#### Signature

```python
def sort_components(
    self, components: list[Type[Component]]
) -> list[Type[Component]]: ...
```

#### See also

- [Component](#component)



## TagComponent

[Show source in component.py:33](../../../src/ecs/core/component.py#L33)

Abstract class for components that represent a data-less Tag

These components do not store any data, and can be used to attach flags
or specific tags to entities.

#### Notes

This component type is best used for properties that do not change frequently.
due to the inefficiency of component removal and addition (changing archetypes),
for frequently changing tags, it is better to use a single boolean component
(flag) that is always attached to the entity, than adding and removing tags from
entities.

#### Examples

```python
>>> class IsPlayer(TagComponent):
>>>     pass
>>>
>>> class Edible(TagComponent):
>>>     pass
```

#### Signature

```python
class TagComponent(Component, ABC): ...
```

#### See also

- [Component](#component)