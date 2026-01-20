# Event

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / Event

> Auto-generated documentation for [core.event](../../../src/ecs/core/event.py) module.

- [Event](#event)
  - [Event](#event-1)
  - [EventBus](#eventbus)
    - [EventBus().handle_event_error](#eventbus()handle_event_error)
    - [EventBus().process_async](#eventbus()process_async)
    - [EventBus().publish_async](#eventbus()publish_async)
    - [EventBus().publish_sync](#eventbus()publish_sync)
    - [EventBus().subscribe](#eventbus()subscribe)
    - [EventBus().unsubscribe](#eventbus()unsubscribe)
    - [EventBus().update](#eventbus()update)

## Event

[Show source in event.py:7](../../../src/ecs/core/event.py#L7)

Base class for events.

#### Signature

```python
class Event: ...
```



## EventBus

[Show source in event.py:19](../../../src/ecs/core/event.py#L19)

Stores and dispatches events.

An event bus that supports both synchronous and asynchronous event dispatch with
double buffering.

Synchronous events are dispatched immediately upon publication.
Asynchronous events are queued and processed in the next update cycle (frame)
via double buffering, ensuring events published during one frame aren't processed
until the following frame.

#### Signature

```python
class EventBus:
    def __init__(self, cmd_buffer: CommandBuffer): ...
```

### EventBus().handle_event_error

[Show source in event.py:142](../../../src/ecs/core/event.py#L142)

#### Signature

```python
def handle_event_error(self, event, func, e): ...
```

### EventBus().process_async

[Show source in event.py:115](../../../src/ecs/core/event.py#L115)

Process all queued asynchronous events.

Uses double buffering to ensure events published in the current frame
aren't processed until the next update cycle.

during processing of a specific event, structural changes are stored in a
command buffer instead of being executed directly.

#### Signature

```python
def process_async(self) -> None: ...
```

### EventBus().publish_async

[Show source in event.py:102](../../../src/ecs/core/event.py#L102)

Publish an event asynchronously.

The event is added to the asynchronous queue and will be processed
in the next update cycle.

#### Arguments

- `event` *Event* - The event to publish.

#### Signature

```python
def publish_async(self, event: _T) -> None: ...
```

### EventBus().publish_sync

[Show source in event.py:83](../../../src/ecs/core/event.py#L83)

Publish an event synchronously.

The event is immediately dispatched to all subscribers registered for its type.

#### Arguments

- `event` *Event* - The event to publish.

#### Signature

```python
def publish_sync(self, event: _T) -> None: ...
```

### EventBus().subscribe

[Show source in event.py:38](../../../src/ecs/core/event.py#L38)

Subscribe a handler to a specific event type.

Whenever an event of that type is dispatched, all subscribers will be called
with that event. The timing depends on whether the publishing was sync or async.

#### Arguments

- `event_type` *Type[Event]* - The type of event to subscribe to.
handler (Callable[[Event], None]): The function to call when the event is
    published.

#### Notes

The handler is stored as a weak reference. This means that the original
reference has to be active for it to be called.
This also means that this feature does not work with `lambda` functions.

#### Signature

```python
def subscribe(self, event_type: Type[_T], handler: Callable[[_T], None]) -> None: ...
```

### EventBus().unsubscribe

[Show source in event.py:70](../../../src/ecs/core/event.py#L70)

Unsubscribe a handler from a specific event type.

#### Arguments

- `event_type` *Type[Event]* - The type of event.
handler (Callable[[Event], None]): The handler to remove.

#### Signature

```python
def unsubscribe(self, event_type: Type[_T], handler: Callable[[_T], None]) -> None: ...
```

### EventBus().update

[Show source in event.py:137](../../../src/ecs/core/event.py#L137)

Update the event bus by processing asynchronous events.

#### Signature

```python
def update(self) -> None: ...
```