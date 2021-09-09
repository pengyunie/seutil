import collections
import unittest
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from recordclass import RecordClass

import seutil as su


class test_io_tempfile(unittest.TestCase):

    PREFIX = "testioprefix"
    SUFFIX = "testiosuffix"
    SEPARATOR = "-X-"

    def test_mktmp(self):
        # Test arguments prefix, suffix, separator
        tmp_file = su.io.mktmp(prefix=self.PREFIX, suffix=self.SUFFIX, separator=self.SEPARATOR)
        self.assertTrue(tmp_file.is_file())
        self.assertTrue(tmp_file.name.startswith(self.PREFIX + self.SEPARATOR))
        self.assertTrue(tmp_file.name.endswith(self.SEPARATOR + self.SUFFIX))

        # Test using the file
        with open(tmp_file, "wt") as f:
            f.write("aaa")

        with open(tmp_file, "wb") as f:
            f.write(b"aaa")

        su.io.rm(tmp_file)

    def test_mktmp_dir(self):
        # Test arguments prefix, suffix, separator
        tmp_dir = su.io.mktmp_dir(prefix=self.PREFIX, suffix=self.SUFFIX, separator=self.SEPARATOR)
        self.assertTrue(tmp_dir.is_dir())
        self.assertTrue(tmp_dir.name.startswith(self.PREFIX + self.SEPARATOR))
        self.assertTrue(tmp_dir.name.endswith(self.SEPARATOR + self.SUFFIX))

        # Test using the dir
        with open(tmp_dir / "test.txt", "wt") as f:
            f.write("aaa")

        su.io.rmdir(tmp_dir)

    def test_mktmp_argument_dir(self):
        # Test argument dir of mktmp, mktmp_dir
        tmp_dir_1 = su.io.mktmp_dir()

        tmp_dir_2 = su.io.mktmp_dir(prefix=self.PREFIX, suffix=self.SUFFIX, separator=self.SEPARATOR, dir=tmp_dir_1)
        self.assertTrue(tmp_dir_2.is_dir())
        self.assertTrue(tmp_dir_2.name.startswith(self.PREFIX + self.SEPARATOR))
        self.assertTrue(tmp_dir_2.name.endswith(self.SEPARATOR + self.SUFFIX))

        tmp_file = su.io.mktmp(prefix=self.PREFIX, suffix=self.SUFFIX, separator=self.SEPARATOR, dir=tmp_dir_1)
        self.assertTrue(tmp_file.is_file())
        self.assertTrue(tmp_file.name.startswith(self.PREFIX + self.SEPARATOR))
        self.assertTrue(tmp_file.name.endswith(self.SEPARATOR + self.SUFFIX))

        su.io.rmdir(tmp_dir_1)


class test_mk_rm_cd(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = su.io.mktmp_dir()

    def tearDown(self) -> None:
        su.io.rmdir(self.temp_dir)

    def test_mkdir(self):
        su.io.mkdir(self.temp_dir / "test1")

    def test_mkdir_fresh(self):
        # fresh=False should not delete existing content
        temp_dir_2 = self.temp_dir / "test2"
        su.io.mkdir(temp_dir_2, fresh=False)
        with open(temp_dir_2 / "test.txt", "wt") as f:
            f.write("aaa")
        su.io.mkdir(temp_dir_2, fresh=False)
        self.assertTrue((temp_dir_2 / "test.txt").is_file())

        # fresh=True should delete existing content
        temp_dir_3 = self.temp_dir / "test3"
        su.io.mkdir(temp_dir_3, fresh=True)
        with open(temp_dir_3 / "test.txt", "wt") as f:
            f.write("aaa")
        su.io.mkdir(temp_dir_3, fresh=True)
        self.assertFalse((temp_dir_3 / "test.txt").is_file())

    def test_mkdir_parents(self):
        # parents=True should create parent files
        su.io.mkdir(self.temp_dir / "test4" / "ddd", parents=True)
        self.assertTrue((self.temp_dir / "test4").is_dir())
        self.assertTrue((self.temp_dir / "test4" / "ddd").is_dir())

        # parents=False should raise error
        with self.assertRaises(FileNotFoundError):
            su.io.mkdir(self.temp_dir / "test5" / "ddd", parents=False)

    def test_rm(self):
        # rm file
        f = su.io.mktmp(dir=self.temp_dir)
        self.assertTrue(f.is_file())
        su.io.rm(f)
        self.assertFalse(f.is_file())

        # rm dir
        d = su.io.mktmp_dir(dir=self.temp_dir)
        self.assertTrue(d.is_dir())
        su.io.rm(d)
        self.assertFalse(d.is_dir())

    def test_rm_missing_ok(self):
        # missing_ok=True should just be fine
        su.io.rm(self.temp_dir / "abcdefg", missing_ok=True)

        # missing_ok=False should raise error
        with self.assertRaises(FileNotFoundError):
            su.io.rm(self.temp_dir / "abcdefg", missing_ok=False)

    def test_rm_force(self):
        d = su.io.mktmp_dir(dir=self.temp_dir)
        su.io.mktmp(dir=d)
        self.assertTrue(d.is_dir())

        # force=False should raise error
        with self.assertRaises(OSError):
            su.io.rm(d, force=False)
        self.assertTrue(d.is_dir())

        # force=True should be fine
        su.io.rm(d, force=True)
        self.assertFalse(d.is_dir())

    def test_rmdir(self):
        # rm dir
        d = su.io.mktmp_dir(dir=self.temp_dir)
        self.assertTrue(d.is_dir())
        su.io.rmdir(d)
        self.assertFalse(d.is_dir())

        # cannot rm file
        f = su.io.mktmp(dir=self.temp_dir)
        self.assertTrue(f.is_file())
        with self.assertRaises(OSError):
            su.io.rmdir(f)

    def test_rmdir_missing_ok(self):
        # missing_ok=True should just be fine
        su.io.rmdir(self.temp_dir / "abcdefg", missing_ok=True)

        # missing_ok=False should raise error
        with self.assertRaises(FileNotFoundError):
            su.io.rmdir(self.temp_dir / "abcdefg", missing_ok=False)

    def test_rmdir_force(self):
        d = su.io.mktmp_dir(dir=self.temp_dir)
        su.io.mktmp(dir=d)
        self.assertTrue(d.is_dir())

        # force=False should raise error
        with self.assertRaises(OSError):
            su.io.rmdir(d, force=False)
        self.assertTrue(d.is_dir())

        # force=True should be fine
        su.io.rmdir(d, force=True)
        self.assertFalse(d.is_dir())

    def test_cd(self):
        d = su.io.mktmp_dir(dir=self.temp_dir)
        self.assertFalse(Path.cwd() == d)
        with su.io.cd(d):
            self.assertTrue(Path.cwd() == d)
        self.assertFalse(Path.cwd() == d)


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


class test_io_dump_load(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = su.io.mktmp_dir()

    def tearDown(self) -> None:
        su.io.rmdir(self.temp_dir)

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
    ]

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

    def test_dump_load(self):
        for fname, fmt, inputs in self.FMTS_INPUTS:
            for inp in inputs:
                self._test_dump_load(fname, fmt, inp)

    def _test_dump_load(self, fname, fmt, inp):
        msg = f"{fname=}, {fmt=}, {inp=}"
        path = self.temp_dir / fname

        su.io.dump(path, inp, fmt=fmt)
        self.assertTrue(path.is_file(), msg=msg)

        loaded = su.io.load(path, fmt=fmt, clz=type(inp), error="raise")
        self.assertEqual(type(inp), type(loaded), msg=msg)
        self.assertEqual(inp, loaded, msg=msg)

        su.io.rm(path)

    TXT_INPUTS_ONELINE = [x.replace("\n", " ") for x in TXT_INPUTS]

    FMTS_INPUTS_LINE_MODE: List[Tuple[str, Optional[su.io.Fmt], List[Any]]] = [
        ("a.txt", su.io.Fmt.txtList, TXT_INPUTS_ONELINE),
        ("a.jsonl", None, TXT_INPUTS_ONELINE + JSON_INPUTS),
        ("a.jsonl", su.io.Fmt.jsonList, TXT_INPUTS_ONELINE + JSON_INPUTS),
    ]

    def test_dump_load_line_mode(self):
        for fname, fmt, inputs in self.FMTS_INPUTS_LINE_MODE:
            for inp in inputs:
                self._test_dump_load_line_mode(fname, fmt, inp)

    def _test_dump_load_line_mode(self, fname, fmt, inp):
        msg = f"{fname=}, {fmt=}, {inp=}"
        path = self.temp_dir / fname
        inp_list = [inp] * 20

        su.io.dump(path, inp_list, fmt=fmt)
        self.assertTrue(path.is_file(), msg=msg)

        # Test iter_line=False
        loaded_list = su.io.load(path, fmt=fmt, clz=type(inp), error="raise", iter_line=False)
        self.assertEqual(list, type(loaded_list), msg=msg)
        self.assertEqual(inp_list, loaded_list, msg=msg)

        # Test iter_line=True
        for loaded in su.io.load(path, fmt=fmt, clz=type(inp), error="raise", iter_line=True):
            self.assertEqual(type(inp), type(loaded), msg=msg)
            self.assertEqual(inp, loaded, msg=msg)

        su.io.rm(path)
