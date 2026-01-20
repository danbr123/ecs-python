# Render

[Ecs-python Index](../../README.md#ecs-python-index) / [Adapters](../index.md#adapters) / [Pygame](./index.md#pygame) / Render

> Auto-generated documentation for [adapters.pygame.render](../../../../src/ecs/adapters/pygame/render.py) module.

- [Render](#render)
  - [DisableRender](#disablerender)
  - [PygameRenderSystem](#pygamerendersystem)
    - [PygameRenderSystem().initialize](#pygamerendersystem()initialize)
    - [PygameRenderSystem().update](#pygamerendersystem()update)
  - [Sprite](#sprite)
  - [Transform](#transform)

## DisableRender

[Show source in render.py:22](../../../../src/ecs/adapters/pygame/render.py#L22)

#### Signature

```python
class DisableRender(Component): ...
```

#### See also

- [Component](../../core/component.md#component)



## PygameRenderSystem

[Show source in render.py:26](../../../../src/ecs/adapters/pygame/render.py#L26)

A basic rendering system that draws Sprites at Transform positions

#### Signature

```python
class PygameRenderSystem(System):
    def __init__(self, *args, **kwargs) -> None: ...
```

#### See also

- [System](../../core/system.md#system)

### PygameRenderSystem().initialize

[Show source in render.py:35](../../../../src/ecs/adapters/pygame/render.py#L35)

#### Signature

```python
def initialize(self, world: World) -> None: ...
```

#### See also

- [World](../../core/world.md#world)

### PygameRenderSystem().update

[Show source in render.py:38](../../../../src/ecs/adapters/pygame/render.py#L38)

#### Signature

```python
def update(self, world: World, dt: float) -> None: ...
```

#### See also

- [World](../../core/world.md#world)



## Sprite

[Show source in render.py:16](../../../../src/ecs/adapters/pygame/render.py#L16)

Standard component for a pygame surface

#### Signature

```python
class Sprite(Component): ...
```

#### See also

- [Component](../../core/component.md#component)



## Transform

[Show source in render.py:10](../../../../src/ecs/adapters/pygame/render.py#L10)

Standard component for position

#### Signature

```python
class Transform(Component): ...
```

#### See also

- [Component](../../core/component.md#component)