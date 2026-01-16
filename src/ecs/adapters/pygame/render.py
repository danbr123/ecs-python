from __future__ import annotations

import pygame

from ...core.component import Component
from ...core.system import System
from ...core.world import World


class Transform(Component):
    """Standard component for position"""

    shape = (2,)  # [x, y]


class Sprite(Component):
    """Standard component for a pygame surface"""

    dtype = object


class DisableRender(Component):
    dtype = bool


class PygameRenderSystem(System):
    """A basic rendering system that draws Sprites at Transform positions"""

    group = "render"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.query = None

    def initialize(self, world: World) -> None:
        self.query = world.query(include=[Transform, Sprite])

    def update(self, world: World, dt: float) -> None:
        screen = world.resources.get_as("pygame.screen", pygame.Surface)
        for _, _, data in self.query.fetch(optional=[DisableRender]):
            positions = data[Transform]
            surfaces = data[Sprite]

            if DisableRender in data:
                is_visible = ~data[DisableRender].astype(bool).ravel()
                positions = positions[is_visible]
                surfaces = surfaces[is_visible]
            screen.blits(zip(surfaces, positions))
