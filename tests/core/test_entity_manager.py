from unittest.mock import Mock

import numpy as np
import pytest

from ecs.core.component import Component, ComponentRegistry, TagComponent
from ecs.core.entity_manager import EntityManager, PendingEntityException


class Position(Component):
    shape = (2,)
    dtype = np.float32


class Velocity(Component):
    shape = (2,)
    dtype = np.float32


class Health(Component):
    shape = (1,)
    dtype = np.int32


class IsPlayer(TagComponent):
    pass


@pytest.fixture
def registry():
    return ComponentRegistry()


@pytest.fixture
def manager(registry):
    return EntityManager(registry, on_arch_created=Mock())


def test_validate_data_valid(manager):
    res = manager._validate_data(Health, 100)
    assert res.shape == (1,)
    assert res.dtype == np.int32
    assert res[0] == 100

    res = manager._validate_data(Position, [1.5, 2.5])
    assert res.shape == (2,)
    assert res.dtype == np.float32
    np.testing.assert_array_equal(res, [1.5, 2.5])

    arr = np.array([10, 20], dtype=np.float32)
    res = manager._validate_data(Position, arr)
    np.testing.assert_array_equal(res, arr)


def test_validate_data_invalid_shape(manager):
    with pytest.raises(ValueError):
        manager._validate_data(Position, [1, 2, 3])


def test_validate_data_invalid_dtype(manager):
    with pytest.raises(ValueError):
        manager._validate_data(Health, "invalid")


def test_validate_tag_returns_none(manager):
    assert manager._validate_data(IsPlayer, "junk") is None


def test_add_entity(manager):
    eid = manager.add({Position: [0, 0], IsPlayer: True})

    assert eid == 0
    assert len(manager.entities_map) == 1

    arch, row = manager.entities_map[eid]
    assert arch.components == {Position, IsPlayer}
    assert row == 0
    manager.on_arch_created.assert_called_once()


def test_remove_entity(manager):
    eid = manager.add({Position: [0, 0]})
    removed = manager.remove(eid)

    assert removed == eid
    assert eid not in manager.entities_map

    with pytest.raises(ValueError):
        manager.remove(eid)


def test_remove_entity_swaps_rows(manager):
    _ = manager.add({Position: [1, 1]})
    e2 = manager.add({Position: [2, 2]})
    e3 = manager.add({Position: [3, 3]})

    manager.remove(e2)

    assert e2 not in manager.entities_map

    arch, row = manager.entities_map[e3]
    assert row == 1
    np.testing.assert_array_equal(arch.storage[Position][1], [3, 3])


def test_reserve_id(manager):
    eid = manager.reserve_id()
    assert eid == 0
    assert manager.entities_map[eid] == (None, None)

    manager.add({Position: [0, 0]}, reserved_id=eid)
    assert manager.entities_map[eid][0] is not None


def test_add_reserved_id_validation(manager):
    eid = manager.reserve_id()

    with pytest.raises(ValueError):
        manager.add({Position: [0, 0]}, reserved_id=999)

    manager.add({Position: [0, 0]}, reserved_id=eid)
    with pytest.raises(ValueError):
        manager.add({Position: [0, 0]}, reserved_id=eid)


def test_deregister_reserved_ids(manager):
    e1 = manager.reserve_id()
    e2 = manager.add({Position: [0, 0]})

    manager.deregister_reserved_ids([e1, e2])

    assert e1 not in manager.entities_map
    assert e2 in manager.entities_map


def test_add_components_changes_archetype(manager):
    e1 = manager.add({Position: [1, 1]})
    original_arch = manager.entities_map[e1][0]

    manager.add_components(e1, {Velocity: [2, 2]})

    new_arch, new_row = manager.entities_map[e1]
    assert new_arch != original_arch
    assert new_arch.components == {Position, Velocity}

    np.testing.assert_array_equal(new_arch.storage[Position][new_row], [1, 1])
    np.testing.assert_array_equal(new_arch.storage[Velocity][new_row], [2, 2])
    assert original_arch.entity_ids[0] == -1


def test_add_components_same_archetype(manager):
    e1 = manager.add({Position: [1, 1], Velocity: [0, 0]})
    original_arch = manager.entities_map[e1][0]

    manager.add_components(e1, {Velocity: [5, 5]})

    current_arch, row = manager.entities_map[e1]
    assert current_arch == original_arch
    np.testing.assert_array_equal(current_arch.storage[Velocity][row], [5, 5])


def test_remove_components(manager):
    e1 = manager.add({Position: [1, 1], Velocity: [2, 2]})
    _ = manager.entities_map[e1][0]

    manager.remove_components(e1, [Velocity])

    new_arch, new_row = manager.entities_map[e1]
    assert new_arch.components == {Position}
    np.testing.assert_array_equal(new_arch.storage[Position][new_row], [1, 1])
    assert Velocity not in new_arch.storage


def test_get_component(manager):
    e1 = manager.add({Position: [10, 20]})

    val = manager.get_component(e1, Position)
    np.testing.assert_array_equal(val, [10, 20])


def test_get_component_errors(manager):
    eid = manager.reserve_id()
    with pytest.raises(PendingEntityException):
        manager.get_component(eid, Position)

    manager.add({Position: [0, 0]}, reserved_id=eid)
    with pytest.raises(ValueError):
        manager.get_component(eid, Velocity)

    with pytest.raises(ValueError):
        manager.get_component(999, Position)


def test_set_component(manager):
    e1 = manager.add({Position: [0, 0]})
    manager.set_component(e1, Position, [5, 5])

    val = manager.get_component(e1, Position)
    np.testing.assert_array_equal(val, [5, 5])


def test_set_component_errors(manager):
    eid = manager.reserve_id()
    with pytest.raises(PendingEntityException):
        manager.set_component(eid, Position, [0, 0])

    manager.add({Position: [0, 0]}, reserved_id=eid)
    with pytest.raises(ValueError):
        manager.set_component(eid, Velocity, [0, 0])
