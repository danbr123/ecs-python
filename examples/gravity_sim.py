"""Example usage of python-ecs framework.

This is an N-body gravity simulator, using the naive N^2 calculation. This demonstrates
the usage of the ecs framework while also stress-testing it with heavy calculations.
This example also uses the PygameApp adapter from `ecs.adapters.pygame`

For efficiency - we use numba for the acceleration calculation.
In a future version - it will also be used for the collision check, currently this is
the bottleneck when collisions are enabled.

How to use:
- Install dependencies:
    - numba
    - pygame
    - numpy <= 2.3.5  (currently required for numba)
    - ecs-python
- run gravity_sim.py

Controls:
- Left mouse click - spawn a single planet
- Right mouse click - spawn a group of planets (PLANET_GROUP_SIZE - default 10)
- C - toggle collision system
- F - toggle FPS view

Sliders:
- Radius - change next spawned planet radius (also affects mass)
- Gravity - gravity constant
- Speed - simulation speed - does not decrease accuracy but affects FPS
- DYNAMIC/LOCKED button - toggle locked flag - if locked - the next planet will be
  locked in place and will not move. locked planets still affect the movement of other
  planets.

"""

import math
import random
from copy import copy
from dataclasses import dataclass
from functools import partial
from typing import Any, Type

import numpy as np
import pygame
from numba import njit, prange

from ecs import Component, Event, System, TagComponent, World
from ecs.adapters.pygame import PygameApp

DEFAULT_G = 0.66743
PHYSICS_FREQUENCY = 600  # physics updates PER SECOND
PLANET_GROUP_SIZE = 10
EPS = 1e-10  # minimum distance between objects - avoid infinite forces


# components


class Locked(TagComponent):
    pass


class Mass(Component):
    dtype = np.float64
    shape = (1,)


class Radius(Component):
    dtype = np.float64
    shape = (1,)


class Velocity(Component):
    dtype = np.float64
    shape = (2,)


class Position(Component):
    dtype = np.float64
    shape = (2,)


class Color(Component):
    shape = (3,)  # [R, G, B]
    dtype = np.float32


# events
@dataclass
class PlanetSpawnEvent(Event):
    position: tuple[float, float]
    velocity: tuple[float, float]
    radius: float
    is_locked: bool


@dataclass
class ToggleSystemEvent(Event):
    system_type: Type[System]


@dataclass
class ResourceChangedEvent(Event):
    key: str
    value: Any


# helper functions


@njit(parallel=True, cache=True)
def calculate_gravity(pos: np.ndarray, mass: np.ndarray, g: float) -> np.ndarray:
    n = pos.shape[0]
    acc = np.zeros((n, 2), dtype=np.float64)
    for i in prange(n):
        for j in range(n):
            if i == j:
                continue
            dx = pos[j, 0] - pos[i, 0]
            dy = pos[j, 1] - pos[i, 1]

            dist_sq = dx * dx + dy * dy + EPS  # add epsilon to avoid infinite forces
            dist = np.sqrt(dist_sq)

            # f = g * mi * mj / r^3 -> a = g * mj / r^3
            a = g * mass[j, 0] / (dist * dist_sq)

            # apply new force on acceleration components
            acc[i, 0] += a * dx
            acc[i, 1] += a * dy
    return acc


def _rad_to_mass(r: float) -> float:
    return (r**3) * 10


def _mass_to_rad(m: float) -> float:
    return math.cbrt(m / 10)


# systems


class AccelerationSystem(System):
    group = "physics"

    def initialize(self, world: World) -> None:
        self.queries["planets"] = world.query(include=[Mass, Position])

    def update(self, world: World, dt: float) -> None:
        g_const = world.resources.get("G", DEFAULT_G)

        array_data = self.queries["planets"].gather()
        if len(array_data["ids"]) == 0:
            return

        # calculate forces using numba
        acc = calculate_gravity(array_data[Position], array_data[Mass], g_const)

        for arch, entities, arch_data in self.queries["planets"].fetch(
            optional=[Velocity, Locked]
        ):
            if Locked not in arch.components and Velocity in arch.components:
                arch_data[Velocity] += acc[array_data["slices"][arch]] * dt


class MovementSystem(System):
    group = "physics"

    def initialize(self, world: World) -> None:
        self.queries["planets"] = world.query(
            include=[Mass, Position, Velocity], exclude=[Locked]
        )

    def update(self, world: World, dt: float) -> None:
        for _, _, data in self.queries["planets"].fetch():
            data[Position] += data[Velocity] * dt


class CollisionSystem(System):
    # TODO - use numba, query.gather
    group = "default"  # update frequency is lower to avoid performance issues

    def initialize(self, world: World) -> None:
        self.queries["planets"] = world.query(
            include=[Mass, Position, Radius, Velocity]
        )

    def update(self, world: World, dt: float) -> None:

        all_ids = []
        all_pos = []
        all_vel = []
        all_mass = []
        all_radius = []
        all_locked_flags = []

        for arch, entities, data in self.queries["planets"].fetch(optional=[Locked]):
            all_ids.append(entities)
            all_pos.append(data[Position])
            all_vel.append(data[Velocity])
            all_mass.append(data[Mass])
            all_radius.append(data[Radius])
            all_locked_flags.append(
                np.ones(len(entities))
                if Locked in arch.components
                else np.zeros(len(entities))
            )

        if not all_ids:
            return

        ids = np.concatenate(all_ids)
        pos = np.concatenate(all_pos)
        vel = np.concatenate(all_vel)
        mass = np.concatenate(all_mass).flatten()
        radius = np.concatenate(all_radius).flatten()
        locked_flags = np.concatenate(all_locked_flags)

        if len(ids) == 1:
            return  # skip if there is one entity

        # calculate collisions
        diff = pos[None, :, :] - pos[:, None, :]
        dist_sq = np.sum(diff**2, axis=2)
        sum_radius = radius[None, :] + radius[:, None]
        collision_mask = dist_sq < (sum_radius**2)
        np.fill_diagonal(collision_mask, False)

        to_remove = []
        for i in range(len(ids)):
            if ids[i] in to_remove:
                continue

            collisions = np.where(collision_mask[i])[0]
            for j in collisions:
                if ids[j] in to_remove:
                    # j already collided and was removed
                    continue
                winner, loser = (i, j) if radius[i] > radius[j] else (j, i)
                winner_id, loser_id = (ids[winner], ids[loser])

                new_mass = mass[winner] + mass[loser]
                new_radius = _mass_to_rad(new_mass)

                # conserve momentum
                new_velocity = (
                    mass[winner] * vel[winner] + mass[loser] * vel[loser]
                ) / new_mass
                if locked_flags[winner]:
                    new_velocity = 0.0
                world.set_component(winner_id, Mass, new_mass)
                world.set_component(winner_id, Radius, new_radius)
                world.set_component(winner_id, Velocity, new_velocity)
                to_remove.append(loser_id)
                if loser == i:
                    break

        for eid in set(to_remove):
            world.cmd_buffer.remove_entity(eid)


class CleanupSystem(System):
    group = "cleanup"

    def initialize(self, world: World) -> None:
        self.queries["planets"] = world.query(include=[Mass, Position])

    def update(self, world: World, dt: float) -> None:
        cleanup_dist_sq = world.resources.get("cleanup_dist", 3000) ** 2
        for _, entities, data in self.queries["planets"].fetch():
            dist_squares = np.sum(data[Position] ** 2, axis=1)
            remove_mask = dist_squares > cleanup_dist_sq
            entities_to_remove = entities[remove_mask]
            for entity in entities_to_remove:
                world.cmd_buffer.remove_entity(entity)


class GravityRenderSystem(System):
    group = "render"

    def initialize(self, world: World):
        self.queries["renderables"] = world.query(include=[Position, Color, Radius])

    def update(self, world: World, dt: float) -> None:
        screen = world.resources.get_as("pygame.screen", pygame.Surface)
        for _, _, data in self.queries["renderables"].fetch():
            pos_batch = data[Position]
            col_batch = data[Color]
            radius = data[Radius]
            for i in range(len(pos_batch)):
                p, col, r = pos_batch[i], col_batch[i], radius[i]
                pygame.draw.circle(
                    screen,
                    (int(col[0]), int(col[1]), int(col[2])),
                    (int(p[0]), int(p[1])),
                    int(r[0]),
                )


class SpawnerSystem(System):
    group = "default"

    def initialize(self, world: World) -> None:
        self._handler = partial(self._spawn, world=world)
        world.event_bus.subscribe(PlanetSpawnEvent, self._handler)

    def update(self, world: World, dt: float) -> None:
        """Skip update - subscriber only"""
        pass

    @staticmethod
    def _spawn(event: PlanetSpawnEvent, world: World) -> None:
        comps = {
            Position: event.position,
            Velocity: event.velocity if not event.is_locked else (0, 0),
            Mass: _rad_to_mass(event.radius),
            Color: np.array(
                [random.randint(100, 255), random.randint(100, 255), 255],
                dtype=np.float32,
            ),
            Radius: event.radius,
        }
        world.cmd_buffer.create_entity(comps)


class WorldManager(System):
    group = "default"

    def initialize(self, world: World) -> None:
        # handlers must be kept alive so the weak reference won't be removed
        self._sys_toggle_handler = partial(
            self._handle_system_toggle_event, world=world
        )
        self._resource_update_handler = partial(
            self._handle_resource_changed_event, world=world
        )

        world.event_bus.subscribe(ToggleSystemEvent, self._sys_toggle_handler)
        world.event_bus.subscribe(ResourceChangedEvent, self._resource_update_handler)

    def update(self, world: World, dt: float) -> None:
        pass

    @staticmethod
    def _handle_system_toggle_event(event: ToggleSystemEvent, world: World) -> None:
        try:
            sys = world.get_system(event.system_type)
            sys.toggle()
        except ValueError:
            return

    @staticmethod
    def _handle_resource_changed_event(
        event: ResourceChangedEvent, world: World
    ) -> None:
        world.resources[event.key] = event.value


class GravitySim(PygameApp):
    MAX_GRAVITY = 10.0
    MAX_RADIUS = 100.0
    MIN_RADIUS = 1.0
    MAX_TIME_SCALE = 10.0

    def on_start(self):
        self.register_group("physics", PHYSICS_FREQUENCY)
        self.register_group("cleanup", 1.0)

        self.world.register_system(AccelerationSystem(priority=0))
        self.world.register_system(MovementSystem(priority=5))
        self.world.register_system(CleanupSystem(priority=10))
        self.world.register_system(CollisionSystem(priority=15))
        self.world.register_system(GravityRenderSystem(priority=20))
        self.world.register_system(SpawnerSystem(priority=30))
        self.world.register_system(WorldManager(priority=30))

        # Defaults
        self.world.resources["G"] = 0.667
        self.world.resources["time_scale"] = 1.0

        self.font = pygame.font.SysFont("Consolas", 14)
        self.dragging = False
        self.start_pos = (0, 0)
        self.selected_r = 20.0
        self.lock_next = False
        self.show_fps = False

        # UI Layout
        self.sidebar_rect = pygame.Rect(1000, 0, 280, 720)
        self.radius_slider = pygame.Rect(1020, 60, 240, 10)
        self.gravity_slider = pygame.Rect(1020, 130, 240, 10)
        self.time_slider = pygame.Rect(1020, 200, 240, 10)
        self.lock_btn = pygame.Rect(1020, 250, 240, 40)

        self.drag_target = None

        # pre-initialize numba to avoid startup lag
        # TODO - find better way to do this
        dummy_pos = np.zeros((2, 2), dtype=np.float64)
        dummy_mass = np.zeros((2, 1), dtype=np.float64)
        calculate_gravity(dummy_pos, dummy_mass, 1.0)

    def on_event(self, event):
        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.radius_slider.inflate(0, 20).collidepoint(mx, my):
                self.drag_target = "radius"
            elif self.gravity_slider.inflate(0, 20).collidepoint(mx, my):
                self.drag_target = "gravity"
            elif self.time_slider.inflate(0, 20).collidepoint(mx, my):
                self.drag_target = "time"
            elif self.lock_btn.collidepoint(mx, my):
                self.lock_next = not self.lock_next
            elif mx < 1000:
                self.dragging = True
                self.start_pos = (mx, my)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                self.world.event_bus.publish_async(ToggleSystemEvent(CollisionSystem))
            if event.key == pygame.K_f:
                self.show_fps = not self.show_fps

        if event.type == pygame.MOUSEBUTTONUP:
            self.drag_target = None
            if self.dragging:
                self.dragging = False
                vx = (mx - self.start_pos[0]) * 0.5
                vy = (my - self.start_pos[1]) * 0.5
                spawn_event = PlanetSpawnEvent(
                    position=self.start_pos,
                    velocity=(vx, vy),
                    radius=self.selected_r,
                    is_locked=self.lock_next,
                )
                if event.button == pygame.BUTTON_LEFT:
                    self.world.event_bus.publish_async(spawn_event)
                else:
                    # right click - spawn X
                    for _ in range(PLANET_GROUP_SIZE):
                        new_spawn_event = copy(spawn_event)
                        new_x = spawn_event.position[0] + (random.random() - 0.5) * 50
                        new_y = spawn_event.position[1] + (random.random() - 0.5) * 50
                        new_spawn_event.position = (new_x, new_y)
                        self.world.event_bus.publish_async(new_spawn_event)

        if event.type == pygame.MOUSEMOTION and self.drag_target:
            if self.drag_target == "radius":
                rel = max(
                    0.0,
                    min(1.0, (mx - self.radius_slider.x) / self.radius_slider.width),
                )
                self.selected_r = self.MIN_RADIUS + rel * (
                    self.MAX_RADIUS - self.MIN_RADIUS
                )

            elif self.drag_target == "gravity":
                rel = max(
                    0.0,
                    min(1.0, (mx - self.gravity_slider.x) / self.gravity_slider.width),
                )
                self.world.event_bus.publish_async(
                    ResourceChangedEvent(key="G", value=rel * self.MAX_GRAVITY)
                )

            elif self.drag_target == "time":
                rel = max(
                    0.0, min(1.0, (mx - self.time_slider.x) / self.time_slider.width)
                )
                self.world.resources["time_scale"] = rel * self.MAX_TIME_SCALE
                self.world.event_bus.publish_async(
                    ResourceChangedEvent(
                        key="time_scale", value=rel * self.MAX_TIME_SCALE
                    )
                )

    def on_post_render(self, screen):
        pygame.draw.rect(screen, (25, 25, 30), self.sidebar_rect)

        # radius slider
        pygame.draw.rect(screen, (50, 50, 60), self.radius_slider)
        rad_range = self.MAX_RADIUS - self.MIN_RADIUS
        rad_rel = (self.selected_r - self.MIN_RADIUS) / rad_range
        rad_handle_x = self.radius_slider.x + rad_rel * self.radius_slider.width
        pygame.draw.circle(
            screen, (200, 200, 200), (int(rad_handle_x), self.radius_slider.centery), 8
        )
        screen.blit(
            self.font.render(f"Radius: {self.selected_r:.1f}", True, (200, 200, 200)),
            (1020, 40),
        )

        # gravity slider
        current_g = self.world.resources.get("G", 0.0)
        pygame.draw.rect(screen, (50, 50, 60), self.gravity_slider)
        grav_rel = current_g / self.MAX_GRAVITY
        grav_handle_x = self.gravity_slider.x + grav_rel * self.gravity_slider.width
        pygame.draw.circle(
            screen,
            (200, 200, 200),
            (int(grav_handle_x), self.gravity_slider.centery),
            8,
        )
        screen.blit(
            self.font.render(f"Gravity: {current_g:.3f}", True, (200, 200, 200)),
            (1020, 110),
        )

        # time slider
        current_time = self.world.resources.get("time_scale", 1.0)
        pygame.draw.rect(screen, (50, 50, 60), self.time_slider)
        time_rel = current_time / self.MAX_TIME_SCALE
        time_handle_x = self.time_slider.x + time_rel * self.time_slider.width
        pygame.draw.circle(
            screen, (200, 200, 200), (int(time_handle_x), self.time_slider.centery), 8
        )
        screen.blit(
            self.font.render(f"Speed: {current_time:.1f}x", True, (200, 200, 200)),
            (1020, 180),
        )

        # lock button
        btn_col = (180, 50, 50) if self.lock_next else (50, 50, 60)
        pygame.draw.rect(screen, btn_col, self.lock_btn, border_radius=4)
        screen.blit(
            self.font.render(
                "LOCKED (STATIC)" if self.lock_next else "DYNAMIC",
                True,
                (255, 255, 255),
            ),
            (1050, 262),
        )

        # stats
        screen.blit(
            self.font.render(
                f"Entities: {len(self.world.entities.entities_map)}",
                True,
                (200, 200, 200),
            ),
            (1020, 10),
        )

        col_enabled = self.world.get_system(CollisionSystem).enabled
        col_text = "ON" if col_enabled else "OFF"
        col_color = (50, 200, 50) if col_enabled else (200, 50, 50)
        screen.blit(
            self.font.render("Collisions (C to toggle): ", True, (200, 200, 200)),
            (1020, 310),
        )
        screen.blit(self.font.render(col_text, True, col_color), (1230, 310))

        if self.show_fps:
            fps = self.clock.get_fps()
            screen.blit(
                self.font.render(f"FPS: {fps:.1f}", True, (0, 255, 0)), (10, 10)
            )

        if self.dragging:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.line(screen, (255, 255, 255), self.start_pos, (mx, my), 1)


if __name__ == "__main__":
    sim = GravitySim(World(), resolution=(1280, 720), fps=60)
    sim.run()
