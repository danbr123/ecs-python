from unittest.mock import Mock, call

import pytest

from src.ecs.core.command_buffer import CommandBuffer
from src.ecs.core.component import Component


class Position(Component):
    pass


@pytest.fixture
def mock_world():
    world = Mock()
    world.entities = Mock()
    world.reserve_id.side_effect = range(100, 200)
    return world


@pytest.fixture
def buffer(mock_world):
    return CommandBuffer(mock_world)


def test_create_entity_reserves_and_queues(buffer, mock_world):
    comps = {Position: [1, 2]}
    eid = buffer.create_entity(comps)

    assert eid == 100
    mock_world.reserve_id.assert_called_once()

    assert len(buffer._commands) == 1
    assert buffer._commands[0] == ("create_entity", comps, 100)
    assert 100 in buffer._reserved_ids
    mock_world.entities.add.assert_not_called()


def test_remove_entity_queues(buffer, mock_world):
    buffer.remove_entity(50)

    assert len(buffer._commands) == 1
    assert buffer._commands[0] == ("remove_entity", 50)


def test_component_modifications_queue(buffer):
    comps = {Position: [1]}
    buffer.add_components(10, comps)
    buffer.remove_components(10, [Position])

    assert buffer._commands[0] == ("add_components", 10, comps)
    assert buffer._commands[1] == ("remove_components", 10, [Position])


def test_flush_execution_order(buffer, mock_world):
    buffer.create_entity({Position: [0]})
    buffer.add_components(100, {Position: [1]})
    buffer.remove_entity(50)

    buffer.flush()

    manager = mock_world.entities
    expected_calls = [
        call.add({Position: [0]}, 100),
        call.add_components(100, {Position: [1]}),
        call.remove(50),
        call.deregister_reserved_ids([100]),
    ]

    assert manager.mock_calls == expected_calls


def test_flush_clears_state(buffer, mock_world):
    buffer.create_entity({})
    assert len(buffer._commands) > 0
    assert len(buffer._reserved_ids) > 0

    buffer.flush()

    assert len(buffer._commands) == 0
    assert len(buffer._reserved_ids) == 0
    mock_world.entities.deregister_reserved_ids.assert_called_with([100])


def test_flush_exception_safety(buffer, mock_world):
    buffer.create_entity({})

    mock_world.entities.remove.side_effect = RuntimeError("Crash")
    buffer.remove_entity(50)

    with pytest.raises(RuntimeError):
        buffer.flush()

    assert len(buffer._reserved_ids) == 0
    mock_world.entities.deregister_reserved_ids.assert_called_with([100])


def test_manual_clear(buffer, mock_world):
    buffer.create_entity({})

    buffer.clear()

    assert len(buffer._commands) == 0
    assert len(buffer._reserved_ids) == 0
    mock_world.entities.deregister_reserved_ids.assert_called_with([100])
    mock_world.entities.add.assert_not_called()
