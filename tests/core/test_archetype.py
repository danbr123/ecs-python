import numpy as np
import pytest

from src.ecs.core.archetype import Archetype
from src.ecs.core.component import Component, TagComponent


class Position(Component):
    shape = (2,)
    dtype = np.float32


class Velocity(Component):
    shape = (2,)
    dtype = np.float32


class IsPlayer(TagComponent):
    pass


@pytest.fixture
def archetype():
    return Archetype(
        components=[Position, Velocity, IsPlayer], signature=1, initial_capacity=4
    )


def test_initialization_structure(archetype):
    """Verify storage is allocated for data components but NOT tags"""
    assert len(archetype) == 0
    assert archetype.components == {Position, Velocity, IsPlayer}

    assert Position in archetype.storage
    assert Velocity in archetype.storage
    assert IsPlayer not in archetype.storage

    assert archetype.storage[Position].shape == (4, 2)
    assert archetype.entity_ids.shape == (4,)
    assert archetype.entity_ids[0] == -1


def test_allocate_reservation(archetype):
    """Verify allocate reserves a row and updates ID mapping"""
    row_0 = archetype.allocate(entity_id=100)
    assert row_0 == 0
    assert len(archetype) == 1
    assert archetype.entity_ids[0] == 100

    row_1 = archetype.allocate(entity_id=101)
    assert row_1 == 1
    assert len(archetype) == 2
    assert archetype.entity_ids[1] == 101


def test_automatic_resize(archetype):
    """Verify capacity doubles when limit reached"""
    for i in range(4):
        archetype.allocate(i)
        archetype.storage[Position][i] = [i, i]

    assert archetype._capacity == 4

    row = archetype.allocate(5)

    assert archetype._capacity == 8
    assert row == 4
    assert len(archetype) == 5

    np.testing.assert_array_equal(archetype.storage[Position][3], [3, 3])
    assert archetype.entity_ids[3] == 3
    assert archetype.entity_ids[4] == 5


def test_remove_last_entity(archetype):
    """Removing the last entity is a simple pop operation (no swap)"""
    archetype.allocate(10)
    archetype.allocate(20)

    archetype.storage[Position][0] = [10, 10]
    archetype.storage[Position][1] = [20, 20]

    moved = archetype.remove_entity(row_id=1)

    assert len(archetype) == 1
    assert moved == -1
    assert archetype.entity_ids[1] == -1


def test_remove_middle_entity_swaps_data(archetype):
    """Removing a middle entity should swap the last entity into its place"""
    archetype.allocate(10)
    archetype.allocate(20)
    archetype.allocate(30)

    archetype.storage[Position][0] = [1, 1]
    archetype.storage[Position][1] = [2, 2]
    archetype.storage[Position][2] = [3, 3]

    moved_id = archetype.remove_entity(row_id=1)

    assert len(archetype) == 2
    assert moved_id == 30

    assert archetype.entity_ids[1] == 30
    assert archetype.entity_ids[2] == -1

    np.testing.assert_array_equal(archetype.storage[Position][1], [3, 3])
    np.testing.assert_array_equal(archetype.storage[Position][0], [1, 1])


def test_remove_out_of_bounds(archetype):
    archetype.allocate(1)

    with pytest.raises(IndexError):
        archetype.remove_entity(5)

    with pytest.raises(IndexError):
        archetype.remove_entity(-1)
