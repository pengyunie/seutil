import collections
import dataclasses
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

import seutil as su
from recordclass import RecordClass


class ExampleNamedTuple1(NamedTuple):
    a: int
    b: float
    c: Tuple[int, int, int] = None
    d: int = 77


ExampleNamedTuple2 = collections.namedtuple("ExampleNamedTuple2", ["e", "f", "g"])


class ExampleRecordClass(RecordClass):
    h: int
    i: float
    j: Dict[str, float] = None
    k: Optional[ExampleNamedTuple2] = None


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


@dataclasses.dataclass
class ExampleDataclass:
    ell: int
    m: float
    n: Dict[str, float] = None
    o: Optional[ExampleNamedTuple2] = None
    p: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.p = str(self.ell) + str(self.m)


TXT_INPUTS: List[Any] = [
    "ABCDEFG 123\n 987",
    "Hello, world!",
]

JSON_INPUTS: List[Any] = [
    None,
    123,
    42.0,
    ["aaaaaa", "EEEEE", 11111],
    ("xxxxxx",),
    {"xyz": 123, "abc": "def"},
    collections.Counter({"a": 3, "c": 4}),
    ExampleNamedTuple1(a=2, b=0.3, c=(1, 2, 3)),
    ExampleNamedTuple2(e=99, f=[3, 5], g=42.0),
    ExampleRecordClass(h=4, i=0.5, j={"a": 4, "b": 6.0}, k=None),
    ExampleOuterDataclass(ExampleInnerDataclass(3)),
    ExampleDataclass(ell=4, m=0.5, n={"a": 4, "b": 6.0}, o=None),
]
# override non-init field to ensure the # overridden value is
# actually loaded rather than recomputed
JSON_INPUTS[-1].p = "overridden"

YAML_INPUTS: List[Any] = [
    {34: 56},
]

PICKLE_INPUTS: List[Any] = [
    12 + 34j,
]

FMTS_INPUTS: List[Tuple[str, Optional[su.io.Fmt], List[Any]]] = [
    ("a.txt", None, TXT_INPUTS),
    ("a.txt", su.io.Fmt.txt, TXT_INPUTS),
    ("a.json", None, TXT_INPUTS + JSON_INPUTS),
    ("a.json", su.io.Fmt.json, TXT_INPUTS + JSON_INPUTS),
    ("a.json", su.io.Fmt.jsonPretty, TXT_INPUTS + JSON_INPUTS),
    ("a.json", su.io.Fmt.jsonNoSort, TXT_INPUTS + JSON_INPUTS),
    ("a.yml", None, TXT_INPUTS + JSON_INPUTS + YAML_INPUTS),
    ("a.yml", su.io.Fmt.yaml, TXT_INPUTS + JSON_INPUTS + YAML_INPUTS),
    ("a.pkl", None, TXT_INPUTS + JSON_INPUTS + YAML_INPUTS + PICKLE_INPUTS),
    ("a.pkl", su.io.Fmt.pickle, TXT_INPUTS + JSON_INPUTS + YAML_INPUTS + PICKLE_INPUTS),
]


def test_dump_load(tmp_path: Path):
    def _test_dump_load(fname, fmt, inp):
        nonlocal tmp_path
        msg = f"{fname=}, {fmt=}, {inp=}"
        path = tmp_path / fname

        su.io.dump(path, inp, fmt=fmt)
        assert path.is_file(), msg

        loaded = su.io.load(path, fmt=fmt, clz=type(inp), error="raise")
        assert type(inp) == type(loaded), msg
        assert inp == loaded, msg

        su.io.rm(path)

    for fname, fmt, inputs in FMTS_INPUTS:
        for inp in inputs:
            _test_dump_load(fname, fmt, inp)


TXT_INPUTS_ONELINE = [x.replace("\n", " ") for x in TXT_INPUTS]

FMTS_INPUTS_LINE_MODE: List[Tuple[str, Optional[su.io.Fmt], List[Any]]] = [
    ("a.txt", su.io.Fmt.txtList, TXT_INPUTS_ONELINE),
    ("a.jsonl", None, TXT_INPUTS_ONELINE + JSON_INPUTS),
    ("a.jsonl", su.io.Fmt.jsonList, TXT_INPUTS_ONELINE + JSON_INPUTS),
]


def test_dump_load_line_mode(tmp_path: Path):
    def _test_dump_load_line_mode(fname, fmt, inp):
        nonlocal tmp_path
        msg = f"{fname=}, {fmt=}, {inp=}"
        path = tmp_path / fname
        inp_list = [inp] * 20

        su.io.dump(path, inp_list, fmt=fmt)
        assert path.is_file(), msg

        # Test iter_line=False
        loaded_list = su.io.load(
            path, fmt=fmt, clz=type(inp), error="raise", iter_line=False
        )
        assert list == type(loaded_list), msg
        assert inp_list == loaded_list, msg

        # Test iter_line=True
        for loaded in su.io.load(
            path, fmt=fmt, clz=type(inp), error="raise", iter_line=True
        ):
            assert type(inp) == type(loaded), msg
            assert inp == loaded, msg

        su.io.rm(path)

    for fname, fmt, inputs in FMTS_INPUTS_LINE_MODE:
        for inp in inputs:
            _test_dump_load_line_mode(fname, fmt, inp)
