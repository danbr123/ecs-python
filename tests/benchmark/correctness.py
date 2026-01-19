import random
import sys

import numpy as np
from numba import njit, prange

from ecs import Component, System, World

N = 100
FRAMES = 60
DT = 0.016
G = 1.0


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
            dist_sq = dx * dx + dy * dy + 1e-10
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


class PhysicsSystem(System):
    def initialize(self, world: World):
        self.queries["p"] = world.query(include=[Mass, Position, Velocity])

    def update(self, world: World, dt: float):
        data = self.queries["p"].gather()
        if len(data["ids"]) == 0:
            return

        acc = calculate_gravity(data[Position], data[Mass], G)

        slices = data["slices"]
        for arch, entities, arch_data in self.queries["p"].fetch():
            if arch in slices:
                sl = slices[arch]
                arch_data[Velocity] += acc[sl] * dt
                arch_data[Position] += arch_data[Velocity] * dt


def get_initial_data(n):
    """Returns identical start data for both engines"""
    random.seed(42)
    np.random.seed(42)
    pos = np.random.rand(n, 2) * 1000
    vel = np.random.rand(n, 2) * 10
    mass = np.random.rand(n, 1) * 100
    return pos, vel, mass


def run_raw_engine():
    pos, vel, mass = get_initial_data(N)

    for _ in range(FRAMES):
        acc = calculate_gravity(pos, mass, G)
        vel += acc * DT
        pos += vel * DT

    return pos


def run_ecs_engine():
    pos, vel, mass = get_initial_data(N)
    world = World()
    sys = PhysicsSystem()
    world.register_system(sys)
    sys.initialize(world)

    ids = []
    for i in range(N):
        eid = world.create_entity({Position: pos[i], Velocity: vel[i], Mass: mass[i]})
        ids.append(eid)

    for _ in range(FRAMES):
        sys.update(world, DT)

    query = world.query(include=[Position])

    final_positions = []
    found_ids = []

    for _, entities, data in query.fetch():
        for i in range(len(entities)):
            found_ids.append(entities[i])
            final_positions.append(data[Position][i])

    found_ids = np.array(found_ids)
    final_positions = np.array(final_positions)

    sort_order = np.argsort(found_ids)
    sorted_pos = final_positions[sort_order]

    return sorted_pos


def main():
    print(f"--- VERIFYING SIMULATION INTEGRITY (N={N}) ---")

    print("Running Raw Engine...")
    res_raw = run_raw_engine()

    print("Running ECS Engine...")
    res_ecs = run_ecs_engine()

    print("\n--- ANALYSIS ---")

    if len(res_ecs) != N:
        print(f"FATAL: Entity Count Mismatch! Expected {N}, got {len(res_ecs)}")
        return

    diff = np.abs(res_raw - res_ecs)
    max_diff = np.max(diff)

    print(f"Max Position Deviation: {max_diff:.10f}")

    if np.allclose(res_raw, res_ecs, atol=1e-12):
        print("\n[SUCCESS] The simulations are identical.")
        sys.exit(0)
    else:
        print("\n[FAILURE] The simulations diverged.")

        print("\nFirst 3 Entities (Raw):")
        print(res_raw[:3])
        print("\nFirst 3 Entities (ECS):")
        print(res_ecs[:3])
        sys.exit(1)


if __name__ == "__main__":
    main()
