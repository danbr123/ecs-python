import argparse
import sys
import time

import numpy as np
from numba import njit, prange

try:
    from src.ecs import Component, System, TagComponent, World
except ImportError:
    print("Error: Could not import 'ecs'")
    sys.exit(1)

DEFAULT_N = [100, 1000, 2500]
DEFAULT_FRAMES = 600
DEFAULT_ROUNDS = 3
G = 0.66743
DT = 1.0 / 600.0
EPS = 1e-10


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
            dist_sq = dx * dx + dy * dy + EPS
            dist = np.sqrt(dist_sq)
            a = g * mass[j, 0] / (dist * dist_sq)
            acc[i, 0] += a * dx
            acc[i, 1] += a * dy
    return acc


class Mass(Component):
    dtype = np.float64
    shape = (1,)


class Velocity(Component):
    dtype = np.float64
    shape = (2,)


class Position(Component):
    dtype = np.float64
    shape = (2,)


class Locked(TagComponent):
    pass


class AccelerationSystem(System):
    def initialize(self, world: World):
        self.queries["planets"] = world.query(include=[Mass, Position])

    def update(self, world: World, dt: float):
        data = self.queries["planets"].gather()
        if len(data.ids) == 0:
            return
        acc = calculate_gravity(data[Position], data[Mass], G)
        slices = data.slices
        for arch, entities, arch_data in self.queries["planets"].fetch(
            optional=[Velocity, Locked]
        ):
            if (
                arch in slices
                and Locked not in arch.components
                and Velocity in arch.components
            ):
                arch_data[Velocity] += acc[slices[arch]] * dt


class MovementSystem(System):
    def initialize(self, world: World):
        self.queries["planets"] = world.query(
            include=[Position, Velocity], exclude=[Locked]
        )

    def update(self, world: World, dt: float):
        for _, _, data in self.queries["planets"].fetch():
            data[Position] += data[Velocity] * dt


def measure_baseline(n, frames):
    pos = np.zeros((n, 2))
    mass = np.ones((n, 1))

    calculate_gravity(pos, mass, G)

    t0 = time.perf_counter()
    for _ in range(frames):
        calculate_gravity(pos, mass, G)
    return time.perf_counter() - t0


def measure_ecs(n, frames):
    world = World()
    acc = AccelerationSystem()
    mov = MovementSystem()
    world.register_system(acc)
    world.register_system(mov)
    acc.initialize(world)
    mov.initialize(world)

    np.random.seed(42)
    for _ in range(n):
        world.create_entity(
            {Position: np.random.rand(2), Velocity: np.zeros(2), Mass: np.ones(1)}
        )

    acc.update(world, DT)
    mov.update(world, DT)

    t0 = time.perf_counter()
    for _ in range(frames):
        acc.update(world, DT)
        mov.update(world, DT)
    return time.perf_counter() - t0


def run_benchmark(n_list, frames, rounds):
    print(f"{'=' * 70}")
    print("ECS SIMULATION PERFORMANCE BENCHMARK")
    print(f"{'=' * 70}")
    print(
        f"{'N':<8} | {'Kernel (ms)':<12} | {'Total (ms)':<12} | "
        f"{'Overhead':<12} | {'Eff %':<8}"
    )
    print(f"{'-' * 70}")

    exit_code = 0

    for n in n_list:
        base_times = []
        for _ in range(rounds):
            base_times.append(measure_baseline(n, frames))
        best_base_s = min(base_times)

        ecs_times = []
        for _ in range(rounds):
            ecs_times.append(measure_ecs(n, frames))
        best_ecs_s = min(ecs_times)

        base_ms = (best_base_s / frames) * 1000
        ecs_ms = (best_ecs_s / frames) * 1000
        overhead_ms = ecs_ms - base_ms

        efficiency = (base_ms / ecs_ms) * 100

        print(
            f"{n:<8} | {base_ms:<12.4f} | {ecs_ms:<12.4f} |"
            f" {overhead_ms:<12.4f} | {efficiency:.1f}%"
        )

        if overhead_ms > 0.1:
            exit_code = 1

    print(f"{'=' * 70}")
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n", type=int, nargs="+", default=DEFAULT_N, help="List of N to test"
    )
    parser.add_argument(
        "--frames", type=int, default=DEFAULT_FRAMES, help="Frames per N"
    )
    parser.add_argument(
        "--rounds", type=int, default=DEFAULT_ROUNDS, help="Rounds per N"
    )
    args = parser.parse_args()

    sys.exit(run_benchmark(args.n, args.frames, args.rounds))
