from unittest.mock import Mock

import numpy as np
import pytest

from ecs.core.archetype import Archetype
from ecs.core.component import Component
from ecs.core.system import System
from ecs.core.world import World


class Position(Component):
    shape = (2,)
    dtype = np.float32


class Velocity(Component):
    shape = (2,)
    dtype = np.float32


class MovementSystem(System):
    def update(self, world, dt):
        pass


class RenderSystem(System):
    group = "render"

    def update(self, world, dt):
        pass


@pytest.fixture
def world():
    return World()


def test_initialization_wires_components(world):
    assert world.registry is not None
    assert world.query_manager is not None
    assert world.entities is not None
    assert world.resources is not None
    assert world.cmd_buffer is not None
    assert world.event_bus is not None
    assert world.systems == []


def test_create_entity_forwarding(world):
    eid = world.create_entity({Position: [1, 2]})
    assert world.entities.entities_map[eid][0].components == {Position}

    val = world.get_component(eid, Position)
    np.testing.assert_array_equal(val, [1, 2])


def test_remove_entity_forwarding(world):
    eid = world.create_entity({Position: [0, 0]})
    world.remove_entity(eid)
    assert eid not in world.entities.entities_map


def test_component_modifications_forwarding(world):
    eid = world.create_entity({Position: [0, 0]})

    world.add_components(eid, {Velocity: [1, 1]})
    assert world.entities.entities_map[eid][0].components == {Position, Velocity}

    world.remove_components(eid, [Position])
    assert world.entities.entities_map[eid][0].components == {Velocity}


def test_set_component_forwarding(world):
    eid = world.create_entity({Position: [0, 0]})
    world.set_component(eid, Position, [5, 5])

    val = world.get_component(eid, Position)
    np.testing.assert_array_equal(val, [5, 5])


def test_reserve_id_forwarding(world):
    eid = world.reserve_id()
    assert eid == 0
    assert world.entities.entities_map[eid] == (None, None)


def test_query_integration_updates_existing_archetypes(world):
    world.create_entity({Position: [0, 0]})

    q = world.query(include=[Position])

    assert len(q.matches) == 1
    assert Position in q.matches[0].components


def test_query_integration_updates_new_archetypes(world):
    q = world.query(include=[Position])
    assert len(q.matches) == 0

    world.create_entity({Position: [0, 0]})

    assert len(q.matches) == 1


def test_system_registration_and_sorting(world):
    sys1 = Mock(spec=System)
    sys1.priority = 10.0

    sys2 = Mock(spec=System)
    sys2.priority = 5.0

    world.register_system(sys1)
    world.register_system(sys2)

    assert world.systems == [sys2, sys1]


def test_get_system_real_classes(world):
    sys1 = MovementSystem()
    world.register_system(sys1)
    assert world.get_system(MovementSystem) is sys1


def test_get_system_missing(world):
    assert world.get_system(MovementSystem) is None


def test_update_calls_systems(world):
    sys = Mock(spec=System)
    sys.priority = 0
    sys.enabled = True
    sys.group = "default"

    world.register_system(sys)
    world.update_systems(dt=1.0)

    sys.update.assert_called_once_with(world, 1.0)


def test_update_respects_groups(world):
    sys_def = Mock(spec=System)
    sys_def.group = "default"
    sys_def.enabled = True
    sys_def.priority = 0

    sys_ren = Mock(spec=System)
    sys_ren.group = "render"
    sys_ren.enabled = True
    sys_ren.priority = 0

    world.register_system(sys_def)
    world.register_system(sys_ren)

    world.update_systems(1.0, group="render")

    sys_def.update.assert_not_called()
    sys_ren.update.assert_called_once()


def test_update_respects_enabled_flag(world):
    sys = Mock(spec=System)
    sys.enabled = False
    sys.priority = 0

    world.register_system(sys)
    world.update_systems(1.0)

    sys.update.assert_not_called()


def test_write_lock_prevention(world):
    class BadSystem(System):
        def update(self, w, dt):
            w.create_entity({Position: [0, 0]})

    world.register_system(BadSystem())

    with pytest.raises(RuntimeError, match="locked"):
        world.update_systems(1.0)


def test_write_lock_allows_command_buffer(world):
    class GoodSystem(System):
        def update(self, w, dt):
            w.cmd_buffer.create_entity({Position: [0, 0]})

    world.register_system(GoodSystem())
    world.update_systems(1.0)

    assert len(world.entities.entities_map) == 1


def test_system_error_handling(world):
    sys = Mock(spec=System)
    sys.enabled = True
    sys.priority = 0
    sys.group = "default"

    sys.update.side_effect = ValueError("System Crash")

    world.register_system(sys)

    world.update_systems(1.0)

    sys.on_error.assert_called_once()
    assert isinstance(sys.on_error.call_args[0][1], ValueError)


def test_full_update_flow(world):
    mock_bus = Mock()
    world.event_bus = mock_bus

    mock_sys = Mock(spec=System)
    mock_sys.enabled = True
    mock_sys.priority = 0
    mock_sys.group = "default"
    world.register_system(mock_sys)

    world.update(1.0)

    mock_sys.update.assert_called_once()
    mock_bus.update.assert_called_once()


def test_flush_is_called(world):
    world.cmd_buffer = Mock()
    world.update(1.0)
    assert world.cmd_buffer.flush.call_count >= 1


def test_get_archetype(world):
    eid = world.create_entity({Position: [0, 0]})
    arch = world.get_archetype(eid)

    assert isinstance(arch, Archetype)
    assert Position in arch.components


def test_get_archetype_invalid(world):
    with pytest.raises(ValueError):
        world.get_archetype(999)
