import numpy as np
import pytest

from src.ecs.core.component import Component, ComponentRegistry, TagComponent


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


def test_component_defaults():
    class DefaultComp(Component):
        pass

    assert DefaultComp.shape == (1,)
    assert DefaultComp.dtype == np.float32


def test_component_custom_schema():
    assert Position.shape == (2,)
    assert Position.dtype == np.float32
    assert Health.shape == (1,)
    assert Health.dtype == np.int32


def test_tag_component_structure():
    assert IsEnemy.shape is None
    assert IsEnemy.dtype is None
    assert issubclass(IsEnemy, Component)


def test_get_bit_assigns_powers_of_two(registry):
    bit_pos = registry.get_bit(Position)
    bit_vel = registry.get_bit(Velocity)
    bit_health = registry.get_bit(Health)

    assert bit_pos == 1
    assert bit_vel == 2
    assert bit_health == 4


def test_get_bit_is_idempotent(registry):
    bit1 = registry.get_bit(Position)
    bit2 = registry.get_bit(Position)
    assert bit1 == bit2


def test_get_bit_invalid_type(registry):
    class NotAComponent:
        pass

    with pytest.raises(TypeError, match="not a subclass of Component"):
        registry.get_bit(NotAComponent)  # type: ignore

    with pytest.raises(TypeError):
        registry.get_bit(123)  # type: ignore


def test_get_signature_basic(registry):
    sig = registry.get_signature([Position, Velocity])
    assert sig == 3


def test_get_signature_empty(registry):
    assert registry.get_signature([]) == 0


@pytest.mark.parametrize(
    "input_list",
    [
        [Position, Velocity],
        [Velocity, Position],
        [Position, Velocity, Position],  # Duplicates
    ],
)
def test_get_signature_consistency(registry, input_list):
    """Ensure order independence and deduplication produce same signature"""
    expected = registry.get_bit(Position) | registry.get_bit(Velocity)
    assert registry.get_signature(input_list) == expected


def test_signature_caching(registry):
    """Verify the cache logic doesn't corrupt subsequent calls"""
    comps = [Position, Health]
    sig1 = registry.get_signature(comps)
    sig2 = registry.get_signature(comps)

    assert sig1 == sig2
    expected = registry.get_bit(Position) | registry.get_bit(Health)
    assert sig1 == expected


def test_sort_components(registry):
    registry.get_bit(Position)
    registry.get_bit(Velocity)
    registry.get_bit(Health)

    input_list = [Health, Position, Velocity]
    sorted_list = registry.sort_components(input_list)

    assert sorted_list == [Position, Velocity, Health]


def test_sort_components_deduplicates(registry):
    registry.get_bit(Position)

    input_list = [Position, Position]
    sorted_list = registry.sort_components(input_list)

    assert sorted_list == [Position]
