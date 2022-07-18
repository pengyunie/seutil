import collections
import dataclasses
import operator
import warnings
from typing import Callable, Dict, NamedTuple, Optional, Tuple

import pytest
import seutil as su
from recordclass import RecordClass
from seutil.io import TData, TObj

_MISSING = object()


def check_serialization_ok(
    obj: TObj,
    data: TData = _MISSING,
    clz: Optional[type] = None,
    obj_eq: Callable[[TObj, TObj], bool] = operator.__eq__,
    data_eq: Callable[[TData, TData], bool] = operator.__eq__,
):
    """Common checks for serialization/deserialization."""
    if clz is None:
        clz = type(obj)
    ser = su.io.serialize(obj)
    if data is not _MISSING:
        assert data_eq(data, ser)
    else:
        print(f"The serialized form of {obj} is: {ser}")
        warnings.warn("Weak serialization check without expected data provided")

    deser = su.io.deserialize(ser, clz)
    assert obj_eq(obj, deser)


@pytest.mark.parametrize(
    "obj",
    [
        # None type
        None,
        # bool
        True,
        False,
        # int
        123,
        # float
        42.24,
        3.1415926535,
        float("inf"),
        # str
        "Hello, world!",
    ],
)
def test_ser_primitives(obj):
    check_serialization_ok(obj=obj, data=obj)


@pytest.mark.xfail(reason="These python primitive types are not supported")
@pytest.mark.parametrize(
    "obj",
    [
        # bytes
        b"Hello, world!",
        # complex
        12 + 3j,
    ],
)
def test_ser_primitives_unsupported(obj):
    check_serialization_ok(obj=obj, data=obj)


@pytest.mark.parametrize(
    "obj",
    [
        [],
        [1, 2, 3],
        [1, 42.24, "Hello, world!"],
        list(range(100)),
        [1, [1, 1], [[1,], [2,], [1,]]],  # fmt: skip
    ],
)
def test_ser_list(obj):
    check_serialization_ok(obj=obj, data=obj)


@pytest.mark.xfail()
def test_ser_ouroboros_list():
    l = []
    l.append(l)
    check_serialization_ok(obj=l)


def test_ser_tuple():
    check_serialization_ok(
        obj=("tuple", "becomes", "list", "after", "ser"),
        data=["tuple", "becomes", "list", "after", "ser"],
    )


def test_ser_tuple_of_list_like():
    check_serialization_ok(
        # fmt: off
        obj=([1, 2.2], (123, "a"), {"only one item otherwise hard to test"}),
        data=[[1, 2.2], [123, "a"], ["only one item otherwise hard to test"]],
        # fmt: on
        clz=Tuple[list, tuple, set],
    )


def test_ser_set():
    check_serialization_ok(
        obj={"set", "becomes", "list", "modulo", "order"},
        data=["set", "becomes", "list", "modulo", "order"],
        data_eq=lambda a, b: sorted(a) == sorted(b),
    )


@pytest.mark.xfail(reason="to be added soon")
def test_ser_deque():
    check_serialization_ok(
        obj=collections.deque([1, 2, 3]),
        data=[1, 2, 3],
    )


@pytest.mark.parametrize(
    "obj",
    [
        {},
        {"a": 1, "b": 2.3, "c": [4, 5, 6], "d": "hello", "e": None},
        {"nested": {"dict": {"should": {"work": True}}}},
    ],
)
def test_ser_dict(obj):
    check_serialization_ok(
        obj=obj,
        data=obj,
    )


def test_ser_defaultdict():
    d = collections.defaultdict(int)
    d["a"] = 1
    check_serialization_ok(
        obj=d,
        data={"a": 1},
    )


def test_ser_counter():
    check_serialization_ok(
        obj=collections.Counter({"a": 1, "b": 2, "c": 3}),
        data={"a": 1, "b": 2, "c": 3},
    )


def test_ser_ordered_dict():
    with pytest.warns(su.io.InfoLossWarning):
        check_serialization_ok(
            obj=collections.OrderedDict([("a", 1), ("b", 2), ("c", 3)]),
            data={"a": 1, "b": 2, "c": 3},
        )


def test_ser_named_tuple_class():
    class ExampleNamedTuple(NamedTuple):
        a: int
        b: float
        c: Tuple[int, int, int] = None
        d: int = 77

    check_serialization_ok(
        obj=ExampleNamedTuple(1, 2.3, (4, 5, 6)),
        data={"a": 1, "b": 2.3, "c": [4, 5, 6], "d": 77},
    )


def test_ser_named_tuple_func():
    ExampleNamedTuple = collections.namedtuple("ExampleNamedTuple", ["e", "f", "g"])
    check_serialization_ok(
        obj=ExampleNamedTuple(99, [3, 5], 42.0),
        data={"e": 99, "f": [3, 5], "g": 42.0},
    )


def test_ser_record_class():
    ExampleNamedTuple = collections.namedtuple("ExampleNamedTuple", ["e", "f", "g"])

    class ExampleRecordClass(RecordClass):
        h: int
        i: float
        j: Dict[str, float] = None
        k: Optional[ExampleNamedTuple] = None

    check_serialization_ok(
        obj=ExampleRecordClass(
            h=4, i=0.5, j={"a": 4, "b": 6.0}, k=ExampleNamedTuple(99, [3, 5], 42.0)
        ),
        data={
            "h": 4,
            "i": 0.5,
            "j": {"a": 4, "b": 6.0},
            "k": {"e": 99, "f": [3, 5], "g": 42.0},
        },
    )


def test_ser_data_class():
    ExampleNamedTuple = collections.namedtuple("ExampleNamedTuple", ["e", "f", "g"])

    @dataclasses.dataclass
    class ExampleDataClass:
        h: int
        i: float
        j: Dict[str, float] = None
        k: Optional[ExampleNamedTuple] = None

    check_serialization_ok(
        obj=ExampleDataClass(
            h=4, i=0.5, j={"a": 4, "b": 6.0}, k=ExampleNamedTuple(99, [3, 5], 42.0)
        ),
        data={
            "h": 4,
            "i": 0.5,
            "j": {"a": 4, "b": 6.0},
            "k": {"e": 99, "f": [3, 5], "g": 42.0},
        },
    )


def test_ser_data_class_customized():
    @dataclasses.dataclass
    class ExampleDataClass:
        a: int
        b: float

        def serialize(self) -> Tuple[int, float]:
            return (self.a, self.b)

        @classmethod
        def deserialize(cls, data: Tuple[int, float]) -> "ExampleDataClass":
            return cls(data[0], data[1])

    check_serialization_ok(
        obj=ExampleDataClass(1, 2.3),
        data=(1, 2.3),
    )


def test_ser_inner_data_class_customized():
    @dataclasses.dataclass
    class ExampleInnerDataclass:
        q: int

        def serialize(self) -> str:
            return str(self.q)

        @classmethod
        def deserialize(cls, data: str) -> "ExampleInnerDataclass":
            return ExampleInnerDataclass(int(data))

    @dataclasses.dataclass
    class ExampleOuterDataclass:
        r: ExampleInnerDataclass

    check_serialization_ok(
        obj=ExampleOuterDataclass(ExampleInnerDataclass(4)),
        data={"r": "4"},
    )


def test_ser_data_class_post_init():
    @dataclasses.dataclass
    class ExampleDataclass:
        a: int
        b: float
        c: str = dataclasses.field(init=False)

        def __post_init__(self):
            self.c = str(self.a) + str(self.b)

    obj = ExampleDataclass(1, 2.3)
    check_serialization_ok(
        obj=obj,
        data={"a": 1, "b": 2.3, "c": "12.3"},
    )

    obj.c = "overridden"
    check_serialization_ok(
        obj=obj,
        data={"a": 1, "b": 2.3, "c": "overridden"},
    )
