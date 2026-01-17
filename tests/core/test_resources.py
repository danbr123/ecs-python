import pytest

from ecs.core.resources import Resources


@pytest.fixture
def res():
    return Resources()


def test_dict_operations(res):
    res["fps"] = 60
    assert res["fps"] == 60
    assert len(res) == 1
    assert "fps" in res

    del res["fps"]
    assert "fps" not in res
    assert len(res) == 0

    with pytest.raises(KeyError):
        _ = res["missing"]


def test_get_defaults(res):
    assert res.get("missing") is None
    assert res.get("missing", 100) == 100

    res["exists"] = 5
    assert res.get("exists") == 5


def test_get_as_success(res):
    res["score"] = 100
    val = res.get_as("score", int)
    assert val == 100
    assert isinstance(val, int)


def test_get_as_type_error(res):
    res["score"] = 100
    with pytest.raises(TypeError):
        res.get_as("score", str)


def test_get_as_missing_key(res):
    with pytest.raises(KeyError):
        res.get_as("missing", int)


def test_set_if_missing(res):
    val = res.set_if_missing("config", True)
    assert val is True
    assert res["config"] is True

    val2 = res.set_if_missing("config", False)
    assert val2 is True
    assert res["config"] is True


def test_iteration(res):
    res["a"] = 1
    res["b"] = 2
    keys = list(res)
    assert "a" in keys
    assert "b" in keys
    assert len(keys) == 2


def test_namespace_prefix_logic(res):
    ns = res.namespace("physics")
    ns["gravity"] = 9.8

    assert res["physics.gravity"] == 9.8
    assert ns["gravity"] == 9.8


def test_namespace_prefix_strips_dot(res):
    ns = res.namespace("render.")
    ns["width"] = 1920

    assert "render.width" in res
    assert "render..width" not in res


def test_namespace_isolation(res):
    ns1 = res.namespace("p1")
    ns2 = res.namespace("p2")

    ns1["score"] = 10
    ns2["score"] = 20

    assert ns1["score"] == 10
    assert ns2["score"] == 20
    assert res["p1.score"] == 10
    assert res["p2.score"] == 20


def test_namespace_get_methods(res):
    ns = res.namespace("sys")
    res["sys.param"] = "value"

    assert ns.get("param") == "value"
    assert ns.get("missing", "default") == "default"


def test_namespace_set_if_missing(res):
    ns = res.namespace("cache")

    val = ns.set_if_missing("size", 1024)
    assert val == 1024
    assert res["cache.size"] == 1024

    val2 = ns.set_if_missing("size", 2048)
    assert val2 == 1024


def test_namespace_delete(res):
    ns = res.namespace("ui")
    ns["color"] = "red"

    del ns["color"]
    assert "ui.color" not in res

    with pytest.raises(KeyError):
        del ns["missing"]


def test_namespace_empty_key_error(res):
    ns = res.namespace("test")
    with pytest.raises(ValueError):
        ns[""] = 1
