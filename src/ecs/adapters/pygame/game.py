from __future__ import annotations

from typing import Optional

try:
    import pygame
except ImportError:
    raise ImportError("Pygame adapter requires pygame to be installed.")

from ...core.world import World


class PygameApp:

    DEFAULT_MIN_FPS = 10

    def __init__(
        self,
        world: World,
        title: str = "ECS Game",
        resolution: tuple[int, int] = (1280, 720),
        fps: int = 60,
    ):
        """Skeleton for standard pygame loop.

        Override and implement hooks with game-specific logic.
        Optional features:
        time_scale (float): Multiplier for game speed (default 1.0).
        min_fps (int): The minimum acceptable frame rate. If the game runs slower
                       than this, the simulation speed will drop to maintain stability.

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
        self.groups_config = {"default": {"interval": 1 / self.fps, "accumulator": 0}}

    def _setup_pygame(self):
        """Pygame initialization and world resources update."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.resolution)
        pygame.display.set_caption(self.title)

        self.world.resources["pygame.screen"] = self.screen
        self.world.resources["pygame.resolution"] = self.resolution

    def register_group(self, name: str, freq: float):
        self.groups_config[name] = {
            "interval": 1.0 / freq if freq > 0 else 0,
            "accumulator": 0.0,
        }

    def run(self):
        self._setup_pygame()
        self.running = True
        self.on_start()

        while self.running:
            render_dt = self.clock.tick(self.fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.on_event(event)

            time_scale = self.world.resources.get("time_scale", 1.0)
            if time_scale > 10.0:
                time_scale = 10.0

            min_fps = self.world.resources.get("min_fps", self.DEFAULT_MIN_FPS)
            if min_fps < 1:
                min_fps = 1
            max_accumulator = 1.0 / min_fps

            for grp, config in self.groups_config.items():
                config["accumulator"] += render_dt * time_scale

                limit = max_accumulator + config["interval"]
                if config["accumulator"] > limit:
                    config["accumulator"] = max_accumulator

                while config["accumulator"] >= config["interval"]:
                    self.world.update(config["interval"], group=grp)
                    config["accumulator"] -= config["interval"]

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
