import gc
from unittest.mock import Mock

import pytest

from ecs.core.command_buffer import CommandBuffer
from ecs.core.event import Event, EventBus


class DamageEvent(Event):
    def __init__(self, amount):
        self.amount = amount


class HealEvent(Event):
    pass


class Handler:
    def __init__(self):
        self.calls = []

    def on_damage(self, event: DamageEvent):
        self.calls.append(event)

    def on_heal(self, event: HealEvent):
        self.calls.append(event)


@pytest.fixture
def cmd_buffer():
    return Mock(spec=CommandBuffer)


@pytest.fixture
def bus(cmd_buffer):
    return EventBus(cmd_buffer)


def test_subscribe_and_publish_sync(bus):
    handler = Handler()
    bus.subscribe(DamageEvent, handler.on_damage)

    event = DamageEvent(10)
    bus.publish_sync(event)

    assert len(handler.calls) == 1
    assert handler.calls[0] is event


def test_subscribe_function_ref(bus):
    calls = []

    def callback(event):
        calls.append(event)

    bus.subscribe(DamageEvent, callback)
    event = DamageEvent(5)
    bus.publish_sync(event)

    assert len(calls) == 1
    assert calls[0] is event


def test_unsubscribe(bus):
    handler = Handler()
    bus.subscribe(DamageEvent, handler.on_damage)
    bus.unsubscribe(DamageEvent, handler.on_damage)

    bus.publish_sync(DamageEvent(10))

    assert len(handler.calls) == 0


def test_unsubscribe_unknown(bus):
    handler = Handler()
    bus.unsubscribe(DamageEvent, handler.on_damage)


def test_garbage_collection_handling(bus):
    handler = Handler()
    bus.subscribe(DamageEvent, handler.on_damage)

    del handler
    gc.collect()

    bus.publish_sync(DamageEvent(10))


def test_publish_async_deferral(bus):
    handler = Handler()
    bus.subscribe(DamageEvent, handler.on_damage)

    event = DamageEvent(10)
    bus.publish_async(event)

    assert len(handler.calls) == 0

    bus.process_async()

    assert len(handler.calls) == 1
    assert handler.calls[0] is event


def test_double_buffering(bus):
    handler = Handler()
    bus.subscribe(DamageEvent, handler.on_damage)

    event1 = DamageEvent(1)
    event2 = DamageEvent(2)

    bus.publish_async(event1)

    bus.process_async()
    assert len(handler.calls) == 1
    assert handler.calls[0] is event1

    bus.publish_async(event2)
    bus.process_async()

    assert len(handler.calls) == 2
    assert handler.calls[1] is event2


def test_publish_invalid_type(bus):
    with pytest.raises(TypeError):
        bus.publish_sync("Not an Event")

    with pytest.raises(TypeError):
        bus.publish_async("Not an Event")


def test_update_flushes_commands(bus, cmd_buffer):
    bus.update()
    cmd_buffer.flush.assert_called_once()


def test_recursive_publish_async(bus):
    handler = Handler()

    def recursive_handler(event):
        handler.calls.append(event)
        if event.amount > 0:
            bus.publish_async(DamageEvent(event.amount - 1))

    bus.subscribe(DamageEvent, recursive_handler)

    bus.publish_async(DamageEvent(1))
    bus.process_async()

    assert len(handler.calls) == 1
    assert handler.calls[0].amount == 1

    bus.process_async()
    assert len(handler.calls) == 2
    assert handler.calls[1].amount == 0


def test_handle_error_sync(bus):
    def crashing_handler(event):
        raise ValueError("Boom")

    bus.subscribe(DamageEvent, crashing_handler)

    with pytest.raises(ValueError, match="Boom"):
        bus.publish_sync(DamageEvent(1))


def test_handle_error_async(bus):
    def crashing_handler(event):
        raise ValueError("Boom")

    bus.subscribe(DamageEvent, crashing_handler)
    bus.publish_async(DamageEvent(1))

    with pytest.raises(ValueError, match="Boom"):
        bus.process_async()
