

TODO

#### Query.gather

Naive use (`Query.fetch` only):

```python
class GravitySystem(System):
    ...
    
    def update(self, world: World, dt: float) -> None:
        g_const = world.resources.get("G", DEFAULT_G)

        # Since gravity is a "global" interaction and different archetypes affect each
        # other, to perform the operation efficiently we cannot apply the calculations
        # on the archetype storage directly (python and numpy overhead would be
        # significant compared to the smaller arrays).
        # instead - we gather all the data in dense arrays and maintain the original
        # slices indices, perform the operations in one go and then scatter the results
        # back to the archetype storages.
        all_positions = []
        all_masses = []
        arch_slices = {}

        curr_idx = 0

        query_res = list(self.queries["planets"].fetch(optional=[Velocity, Locked]))
        for arch, entities, arch_data in query_res:
            all_positions.append(arch_data[Position])
            all_masses.append(arch_data[Mass])
            added = len(entities)
            arch_slices[arch] = (curr_idx, curr_idx + added)
            curr_idx += added

        if not all_positions:
            return

        positions = np.concatenate(all_positions)
        masses = np.concatenate(all_masses)

        # calculate forces using numba
        acc = calculate_gravity(positions, masses, g_const)

        for arch, entities, arch_data in query_res:
            if Locked not in arch.components and Velocity in arch.components:
                arch_data[Velocity] += acc[arch_slices[arch][0]: arch_slices[arch][1]] * dt
```

With `Query.gather`:
```python
class GravitySystem(System):
    ...

    def update(self, world: World, dt: float) -> None:
        g_const = world.resources.get("G", DEFAULT_G)

        gather_results = self.queries["planets"].gather()
        if len(gather_results.ids) == 0:
            return

        # calculate forces using numba
        acc = calculate_gravity(gather_results[Position], gather_results[Mass], g_const)

        for arch, entities, arch_data in self.queries["planets"].fetch(
            optional=[Velocity, Locked]
        ):
            if (arch in gather_results.slices.keys() and Locked not in arch.components 
                and Velocity in arch.components):
                arch_data[Velocity] += acc[gather_results.slices[arch]] * dt

```