import numpy as np
import pytest

from ecs.core.archetype import Archetype
from ecs.core.component import Component, ComponentRegistry, TagComponent
from ecs.core.query import Query, QueryManager


class Position(Component):
    shape = (2,)
    dtype = np.float32


class Velocity(Component):
    shape = (2,)
    dtype = np.float32


class Health(Component):
    shape = (1,)
    dtype = np.int32


class IsEnemy(TagComponent):
    pass


class IsDead(TagComponent):
    pass


@pytest.fixture
def registry():
    return ComponentRegistry()


@pytest.fixture
def manager(registry):
    return QueryManager(registry)


def create_archetype(registry, components, capacity=10, count=0):
    sig = registry.get_signature(components)
    arch = Archetype(components, sig, initial_capacity=capacity)
    for i in range(count):
        arch.allocate(i)
        for comp in components:
            if not issubclass(comp, TagComponent):
                if len(comp.shape) == 1:
                    arch.storage[comp][i] = np.ones(comp.shape, dtype=comp.dtype) * i
    return arch


def test_query_match_include(registry):
    q = Query(include=[Position], exclude=None, registry=registry)

    arch_pos = create_archetype(registry, [Position])
    arch_pos_vel = create_archetype(registry, [Position, Velocity])
    arch_vel = create_archetype(registry, [Velocity])

    q.try_add(arch_pos)
    q.try_add(arch_pos_vel)
    q.try_add(arch_vel)

    assert arch_pos in q.matches
    assert arch_pos_vel in q.matches
    assert arch_vel not in q.matches


def test_query_match_exclude(registry):
    q = Query(include=[Position], exclude=[IsEnemy], registry=registry)

    arch_pos = create_archetype(registry, [Position])
    arch_enemy = create_archetype(registry, [Position, IsEnemy])

    q.try_add(arch_pos)
    q.try_add(arch_enemy)

    assert arch_pos in q.matches
    assert arch_enemy not in q.matches


def test_query_idempotent_add(registry):
    q = Query(include=[Position], exclude=None, registry=registry)
    arch = create_archetype(registry, [Position])

    q.try_add(arch)
    q.try_add(arch)

    assert len(q.matches) == 1


def test_fetch_yields_correct_data(registry):
    q = Query(include=[Position], exclude=None, registry=registry)
    arch = create_archetype(registry, [Position], count=5)

    q.try_add(arch)

    results = list(q.fetch())
    assert len(results) == 1

    matched_arch, ids, data = results[0]
    assert matched_arch == arch
    assert len(ids) == 5
    assert Position in data
    assert data[Position].shape == (5, 2)


def test_fetch_optional_component(registry):
    q = Query(include=[Position], exclude=None, registry=registry)
    arch1 = create_archetype(registry, [Position], count=2)
    arch2 = create_archetype(registry, [Position, Velocity], count=2)

    q.try_add(arch1)
    q.try_add(arch2)

    results = list(q.fetch(optional=[Velocity]))
    assert len(results) == 2

    for arch, _, data in results:
        assert Position in data
        if arch == arch2:
            assert Velocity in data
        else:
            assert Velocity not in data


def test_fetch_excludes_tags_from_data(registry):
    q = Query(include=[Position, IsEnemy], exclude=None, registry=registry)
    arch = create_archetype(registry, [Position, IsEnemy], count=1)
    q.try_add(arch)

    results = list(q.fetch())
    _, _, data = results[0]

    assert Position in data
    assert IsEnemy not in data


def test_gather_structure(registry):
    q = Query(include=[Position], exclude=None, registry=registry)

    arch1 = create_archetype(registry, [Position], count=2)  # 0, 1
    arch2 = create_archetype(registry, [Position, Velocity], count=3)  # 0, 1, 2

    q.try_add(arch1)
    q.try_add(arch2)

    res = q.gather()

    assert len(res["ids"]) == 5
    assert res["slices"][arch1] == slice(0, 2, None)
    assert res["slices"][arch2] == slice(2, 5, None)
    assert res[Position].shape == (5, 2)

    # Check data content (based on create_archetype filling logic)
    # arch1 filled with 0, 1
    # arch2 filled with 0, 1, 2
    expected_col0 = np.concatenate(
        [np.array([0, 1], dtype=np.float32), np.array([0, 1, 2], dtype=np.float32)]
    )
    np.testing.assert_array_equal(res[Position][:, 0], expected_col0)


def test_gather_optional_tags(registry):
    q = Query(include=[Position], exclude=None, registry=registry)

    arch_base = create_archetype(registry, [Position], count=2)
    arch_enemy = create_archetype(registry, [Position, IsEnemy], count=2)

    q.try_add(arch_base)
    q.try_add(arch_enemy)

    res = q.gather(optional=[IsEnemy])

    assert IsEnemy in res
    assert res[IsEnemy].dtype == np.bool_

    s1 = res["slices"][arch_base]
    s2 = res["slices"][arch_enemy]

    assert not np.any(res[IsEnemy][s1])
    assert np.all(res[IsEnemy][s2])


def test_gather_invalid_optional(registry):
    q = Query(include=[Position], exclude=None, registry=registry)
    with pytest.raises(ValueError):
        q.gather(optional=[Velocity])


def test_gather_empty(registry):
    q = Query(include=[Position], exclude=None, registry=registry)
    res = q.gather()

    assert len(res["ids"]) == 0
    assert len(res["slices"]) == 0
    assert res[Position].shape == (0, 2)


def test_gather_includes_tags(registry):
    q = Query(include=[IsEnemy], exclude=None, registry=registry)
    arch = create_archetype(registry, [IsEnemy], count=5)
    q.try_add(arch)

    res = q.gather()

    assert IsEnemy in res
    assert np.all(res[IsEnemy])
    assert len(res["ids"]) == 5


def test_manager_get_query_caching(manager):
    q1, is_new1 = manager.get_query([Position], None)
    q2, is_new2 = manager.get_query([Position], None)

    assert q1 is q2
    assert is_new1 is True
    assert is_new2 is False


def test_manager_distinct_queries(manager):
    q1, _ = manager.get_query([Position], None)
    q2, _ = manager.get_query([Position, Velocity], None)
    q3, _ = manager.get_query([Position], [IsEnemy])

    assert q1 is not q2
    assert q1 is not q3


def test_manager_on_arch_created(manager, registry):
    q, _ = manager.get_query([Position], None)

    arch = create_archetype(registry, [Position])
    manager.on_arch_created(arch)

    assert arch in q.matches
