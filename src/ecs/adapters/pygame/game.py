from __future__ import annotations

import time
from typing import Optional

import pygame

from ...core.world import World


class PygameApp:

    MAX_ACCUMULATOR = 0.1
    TIME_BUDGET = 0.01

    def __init__(
        self,
        world: World,
        title: str = "ECS Game",
        resolution: tuple[int, int] = (1280, 720),
        fps: int = 60,
    ):
        """Skeleton for standard pygame loop.

        Override and implement hooks with game-specific logic.

        Args:
             world (World): World instance
             title (str): Title of the game
             resolution (tuple[int, int]): Resolution of the game
             fps (int): Target FPS for render system updates
        """

        self.world = world
        self.title = title
        self.resolution = resolution
        self.fps = fps
        self.running = False
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.groups_config = {}

    def _setup_pygame(self):
        """Pygame initialization and world resources update."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.resolution)
        pygame.display.set_caption(self.title)

        self.world.resources["pygame.screen"] = self.screen
        self.world.resources["pygame.resolution"] = self.resolution

    def register_group(self, name: str, freq: float):
        self.groups_config[name] = {
            "frequency": 1.0 / freq if freq > 0 else 0,
            "accumulator": 0.0,
        }

    def run(self):
        self._setup_pygame()
        self.running = True
        self.on_start()

        while self.running:
            render_dt = self.clock.tick(self.fps) / 1000.0
            frame_start_time = time.perf_counter()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.on_event(event)

            for grp, config in self.groups_config.items():
                config["accumulator"] += render_dt
                if config["accumulator"] > self.MAX_ACCUMULATOR:
                    config["accumulator"] = self.MAX_ACCUMULATOR
                while config["accumulator"] >= config["frequency"]:
                    self.world.update(config["frequency"], group=grp)
                    config["accumulator"] -= config["frequency"]

                    if (time.perf_counter() - frame_start_time) > self.TIME_BUDGET:
                        break
            self.screen.fill((0, 0, 0))
            self.on_pre_render(screen=self.screen)
            self.world.update(render_dt, group="render")
            self.on_post_render(screen=self.screen)

            pygame.display.flip()

    # --- User Hooks ---

    def on_start(self):
        """Run at the start of the game loop (register systems, initial entities...)"""
        pass

    def on_event(self, event: pygame.event.Event):
        """Handle specific Pygame events."""
        pass

    def on_update(self, dt: float):
        """Run before ECS systems run."""
        pass

    def on_pre_render(self, screen: pygame.Surface):
        """Drawing that isn't handled by an ECS System."""
        pass

    def on_post_render(self, screen: pygame.Surface):
        """Drawing that isn't handled by an ECS System."""
        pass

    def on_shutdown(self):
        """Override for cleanup."""
        pass
