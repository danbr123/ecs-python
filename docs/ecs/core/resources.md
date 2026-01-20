# Resources

[Ecs-python Index](../README.md#ecs-python-index) / [Core](./index.md#core) / Resources

> Auto-generated documentation for [core.resources](../../../src/ecs/core/resources.py) module.

- [Resources](#resources)
  - [ResourceView](#resourceview)
    - [ResourceView().get](#resourceview()get)
    - [ResourceView().set_if_missing](#resourceview()set_if_missing)
  - [Resources](#resources-1)
    - [Resources().get](#resources()get)
    - [Resources().get_as](#resources()get_as)
    - [Resources().namespace](#resources()namespace)
    - [Resources().set_if_missing](#resources()set_if_missing)

## ResourceView

[Show source in resources.py:77](../../../src/ecs/core/resources.py#L77)

A namespaced view over Resources: keys are stored as 'prefix.key'

#### Signature

```python
class ResourceView: ...
```

### ResourceView().get

[Show source in resources.py:99](../../../src/ecs/core/resources.py#L99)

#### Signature

```python
def get(self, key: str, default: Any = None) -> Any: ...
```

### ResourceView().set_if_missing

[Show source in resources.py:102](../../../src/ecs/core/resources.py#L102)

#### Signature

```python
def set_if_missing(self, key: str, value: Any) -> Any: ...
```



## Resources

[Show source in resources.py:10](../../../src/ecs/core/resources.py#L10)

Thin wrapper around a dict for ECS 'global state'

can be used to store states such as render view, camera, event queues,
input snapshot, etc.

The cass provides namespacing via dot-keys ("render.view", "audio.volume").

#### Signature

```python
class Resources(MutableMapping[str, Any]):
    def __init__(self) -> None: ...
```

### Resources().get

[Show source in resources.py:24](../../../src/ecs/core/resources.py#L24)

#### Signature

```python
def get(self, key: str, default: Optional[Any] = None) -> Any: ...
```

### Resources().get_as

[Show source in resources.py:27](../../../src/ecs/core/resources.py#L27)

Retrieve a value with an explicit type for safety or IDE auto-completion

#### Signature

```python
def get_as(self, key: str, type_hint: Type[T]) -> T: ...
```

#### See also

- [T](#t)

### Resources().namespace

[Show source in resources.py:56](../../../src/ecs/core/resources.py#L56)

Create a namespaced view of the resources

Accessing a key 'key' in the namespace will access 'prefix.key' in
the original resource data.

#### Examples

```python
>>> r = Resources()
>>> namespace1 = r.namespace("ns1")
>>> namespace2 = r.namespace("ns2")
>>> namespace1["fps"] = 60
>>> namespace2["fps"] = 30
>>> namespace1["fps"]  # 60
>>> r["ns2.fps"]  # 30
```

#### Signature

```python
def namespace(self, prefix: str) -> "ResourceView": ...
```

### Resources().set_if_missing

[Show source in resources.py:52](../../../src/ecs/core/resources.py#L52)

Set value if one doesn't exist

#### Signature

```python
def set_if_missing(self, key: str, value: Any) -> Any: ...
```