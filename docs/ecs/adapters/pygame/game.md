# Game

[Ecs-python Index](../../README.md#ecs-python-index) / [Adapters](../index.md#adapters) / [Pygame](./index.md#pygame) / Game

> Auto-generated documentation for [adapters.pygame.game](../../../../src/ecs/adapters/pygame/game.py) module.

- [Game](#game)
  - [PygameApp](#pygameapp)
    - [PygameApp().on_event](#pygameapp()on_event)
    - [PygameApp().on_post_render](#pygameapp()on_post_render)
    - [PygameApp().on_pre_render](#pygameapp()on_pre_render)
    - [PygameApp().on_shutdown](#pygameapp()on_shutdown)
    - [PygameApp().on_start](#pygameapp()on_start)
    - [PygameApp().on_update](#pygameapp()on_update)
    - [PygameApp().register_group](#pygameapp()register_group)
    - [PygameApp().run](#pygameapp()run)

## PygameApp

[Show source in game.py:13](../../../../src/ecs/adapters/pygame/game.py#L13)

#### Signature

```python
class PygameApp:
    def __init__(
        self,
        world: World,
        title: str = "ECS Game",
        resolution: tuple[int, int] = (1280, 720),
        fps: int = 60,
    ): ...
```

#### See also

- [World](../../core/world.md#world)

### PygameApp().on_event

[Show source in game.py:108](../../../../src/ecs/adapters/pygame/game.py#L108)

Handle specific Pygame events.

#### Signature

```python
def on_event(self, event: pygame.event.Event): ...
```

### PygameApp().on_post_render

[Show source in game.py:120](../../../../src/ecs/adapters/pygame/game.py#L120)

Drawing that isn't handled by an ECS System.

#### Signature

```python
def on_post_render(self, screen: pygame.Surface): ...
```

### PygameApp().on_pre_render

[Show source in game.py:116](../../../../src/ecs/adapters/pygame/game.py#L116)

Drawing that isn't handled by an ECS System.

#### Signature

```python
def on_pre_render(self, screen: pygame.Surface): ...
```

### PygameApp().on_shutdown

[Show source in game.py:124](../../../../src/ecs/adapters/pygame/game.py#L124)

Override for cleanup.

#### Signature

```python
def on_shutdown(self): ...
```

### PygameApp().on_start

[Show source in game.py:104](../../../../src/ecs/adapters/pygame/game.py#L104)

Run at the start of the game loop (register systems, initial entities...)

#### Signature

```python
def on_start(self): ...
```

### PygameApp().on_update

[Show source in game.py:112](../../../../src/ecs/adapters/pygame/game.py#L112)

Run before ECS systems run.

#### Signature

```python
def on_update(self, dt: float): ...
```

### PygameApp().register_group

[Show source in game.py:57](../../../../src/ecs/adapters/pygame/game.py#L57)

#### Signature

```python
def register_group(self, name: str, freq: float): ...
```

### PygameApp().run

[Show source in game.py:63](../../../../src/ecs/adapters/pygame/game.py#L63)

#### Signature

```python
def run(self): ...
```