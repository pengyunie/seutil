import shutil
import unittest
import tempfile
from enum import Enum
from pathlib import Path
from typing import *

from recordclass import RecordClass

from seutil import IOUtils
from .TestSupport import TestSupport


class test_IOUtils(unittest.TestCase):

    def load_plain(self, path: Path) -> str:
        """
        Loads a file's content in plain text using standard library only. Utility method.
        """
        with open(path, "r") as f:
            return f.read()

    def rm(self, *paths: Path):
        """
        Removes one or more files or directories using standard library only. Utility method.
        """
        for path in paths:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    def test_cd(self):
        with TestSupport.get_playground_path():
            oldpath = Path.cwd()
            testpath = Path("./aaa").resolve()
            testpath.mkdir()
            with IOUtils.cd(testpath):
                # Checks if changed directory successfully
                self.assertEqual(testpath, Path.cwd())
            # end with
            # Checks if returned to old directory successfully
            self.assertEqual(oldpath, Path.cwd())
        # end with
        return

    ### Jsonfy & Dejsonfy

    def test_jsonfy_basic(self):
        self.assertEqual("aaa", IOUtils.jsonfy("aaa"))
        self.assertEqual(42, IOUtils.jsonfy(42))
        self.assertEqual(1.111, IOUtils.jsonfy(1.111))
        self.assertEqual([1, 2.0, "ccc"], IOUtils.jsonfy([1, 2.0, "ccc"]))
        self.assertEqual({1, 2.0, "ccc"}, set(IOUtils.jsonfy({1, 2.0, "ccc"})))
        self.assertEqual({"f1": 1, "f2": 2.0, "f3": "ccc"}, IOUtils.jsonfy({"f1": 1, "f2": 2.0, "f3": "ccc"}))
        return

    def test_dejsonfy_basic(self):
        self.assertEqual("aaa", IOUtils.dejsonfy("aaa"))
        self.assertEqual(42, IOUtils.dejsonfy(42))
        self.assertEqual(1.111, IOUtils.dejsonfy(1.111))
        self.assertEqual([1, 2.0, "ccc"], IOUtils.dejsonfy([1, 2.0, "ccc"]))
        self.assertEqual({"f1": 1, "f2": 2.0, "f3": "ccc"}, IOUtils.dejsonfy({"f1": 1, "f2": 2.0, "f3": "ccc"}))
        return

    def test_dejsonfy_seqs(self):
        self.assertEqual([1, 2, 3], IOUtils.dejsonfy([1, 2, 3], List[int]))
        self.assertEqual((1, 2, 3), IOUtils.dejsonfy([1, 2, 3], Tuple[int, int, int]))
        self.assertEqual({1, 2, 3}, IOUtils.dejsonfy([1, 2, 3], Set[int]))
        return

    ### Jsonfy & Dejsonfy X RecordClass

    class ExampleSimpleRecordClass(RecordClass):
        f: int = 1

    class ExampleRecordClass(RecordClass):
        field_str: str = ""
        field_int: int = 1
        field_int_2: int = 2
        field_list: List[int] = None
        nested_rc: "test_IOUtils.ExampleSimpleRecordClass" = None

    def test_jsonfy_record_class(self):
        example_obj = test_IOUtils.ExampleRecordClass(field_str="aaa", field_int=42, field_list=[1,2], nested_rc=test_IOUtils.ExampleSimpleRecordClass())
        jsonfied = IOUtils.jsonfy(example_obj)
        self.assertTrue(jsonfied.get("field_str") == "aaa")
        self.assertTrue(jsonfied.get("field_int") == 42)
        self.assertTrue(jsonfied.get("field_list") == [1,2])
        self.assertTrue(jsonfied.get("nested_rc").get("f") == 1)
        return

    def test_dejsonfy_record_class(self):
        example_obj = test_IOUtils.ExampleRecordClass(field_str="aaa", field_int=42, field_int_2=66, field_list=[1,2], nested_rc=test_IOUtils.ExampleSimpleRecordClass(f=225))
        dejsonfied = IOUtils.dejsonfy({"field_str": "aaa", "field_int": 42, "field_int_2": "66", "field_list": [1, 2], "nested_rc": {"f": 225}}, test_IOUtils.ExampleRecordClass)
        self.assertEqual(example_obj, dejsonfied)
        return

    ### Jsonfy & Dejsonfy X Enum

    class ExampleEnum(Enum):
        Item1 = 1
        Item3 = 3
        ItemM1 = -1

    def test_jsonfy_enum(self):
        example_obj = test_IOUtils.ExampleEnum.Item1
        jsonfied = IOUtils.jsonfy(example_obj)
        self.assertTrue(jsonfied, example_obj.value)
        return

    def test_dejsonfy_enum(self):
        example_obj = test_IOUtils.ExampleEnum.Item3
        dejsonfied = IOUtils.dejsonfy(3, test_IOUtils.ExampleEnum)
        self.assertEqual(example_obj, dejsonfied)
        return

    def test_format_json_list(self):
        """
        Tests for IOUtils.Format.jsonList
        """
        obj = ["abcde", [1, 2, 3], {"abc": "def"}]
        path = Path(tempfile.mktemp())
        expected = '"abcde"\n[1, 2, 3]\n{"abc": "def"}\n'

        # Test dump
        IOUtils.dump(path, obj, IOUtils.Format.jsonList)
        self.assertEqual(expected, self.load_plain(path))

        # Test load
        loaded = IOUtils.load(path, IOUtils.Format.jsonList)
        self.assertEqual(obj, loaded)

        # Test append
        IOUtils.dump(path, obj, IOUtils.Format.jsonList, append=True)
        self.assertEqual(expected*2, self.load_plain(path))

        self.rm(path)

    def test_format_txt_list(self):
        """
        Tests for IOUtils.Format.txtList
        """
        obj = ["abcde", "12345", "x y z"]
        path = Path(tempfile.mktemp())
        expected = "abcde\n12345\nx y z\n"

        # Test dump
        IOUtils.dump(path, obj, IOUtils.Format.txtList)
        self.assertEqual(expected, self.load_plain(path))

        # Test load
        loaded = IOUtils.load(path, IOUtils.Format.txtList)
        self.assertEqual(obj, loaded)

        # Test append
        IOUtils.dump(path, obj, IOUtils.Format.txtList, append=True)
        self.assertEqual(expected*2, self.load_plain(path))

        self.rm(path)

    def test_format_yaml(self):
        """
        Tests for IOUtils.Format.yaml
        """
        objs = [
            42.001,
            "aaa",
            [13, "24", 56.7],
            {"name": "K", "job": "Y"},
        ]
        exp_strs = [
            "42.001\n...\n",
            "aaa\n...\n",
            "- 13\n- '24'\n- 56.7\n",
            "job: Y\nname: K\n",  # dictionary are forced to be sorted
        ]

        for obj, exp_str in zip(objs, exp_strs):
            path = Path(tempfile.mktemp())

            # Test dump
            IOUtils.dump(path, obj, IOUtils.Format.yaml)
            self.assertEqual(exp_str, self.load_plain(path))

            # Test load
            loaded = IOUtils.load(path, IOUtils.Format.yaml)
            self.assertEqual(obj, loaded)

            self.rm(path)


if __name__ == '__main__':
    unittest.main()
