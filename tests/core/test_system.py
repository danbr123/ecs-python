from unittest.mock import Mock

import pytest

from ecs.core.system import System
from ecs.core.world import World


class ConcreteSystem(System):
    def update(self, world: World, dt: float) -> None:
        pass


class CustomGroupSystem(System):
    group = "physics"

    def update(self, world: World, dt: float) -> None:
        pass


@pytest.fixture
def world_mock():
    return Mock(spec=World)


def test_abstract_instantiation():
    with pytest.raises(TypeError):
        System()  # type: ignore


def test_initialization_defaults():
    sys = ConcreteSystem()
    assert sys.priority == 10.0
    assert sys.enabled is True
    assert sys.name == "ConcreteSystem"
    assert sys.queries == {}
    assert sys.group == "default"


def test_initialization_custom():
    sys = ConcreteSystem(priority=5.5, enabled=False, name="TestSys")
    assert sys.priority == 5.5
    assert sys.enabled is False
    assert sys.name == "TestSys"


def test_group_override():
    sys = CustomGroupSystem()
    assert sys.group == "physics"


def test_enable_disable():
    sys = ConcreteSystem(enabled=True)

    sys.disable()
    assert not sys.enabled

    sys.enable()
    assert sys.enabled


def test_toggle():
    sys = ConcreteSystem(enabled=True)

    sys.toggle()
    assert not sys.enabled

    sys.toggle()
    assert sys.enabled


def test_lifecycle_hooks(world_mock):
    sys = ConcreteSystem()
    sys.initialize(world_mock)
    sys.shutdown(world_mock)


def test_on_error_default_behavior(world_mock):
    sys = ConcreteSystem()
    error = RuntimeError("Crash")

    with pytest.raises(RuntimeError, match="Crash"):
        sys.on_error(world_mock, error)
