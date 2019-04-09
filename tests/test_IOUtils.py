from enum import Enum
import unittest
from pathlib import Path
from recordclass import RecordClass
from typing import *

from seutil import IOUtils
from .TestSupport import TestSupport


class test_IOUtils(unittest.TestCase):

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
        self.assertEqual([1, 2.0, "ccc"], IOUtils.jsonfy({1, 2.0, "ccc"}))
        self.assertEqual({"f1": 1, "f2": 2.0, "f3": "ccc"}, IOUtils.jsonfy({"f1": 1, "f2": 2.0, "f3": "ccc"}))
        return

    def test_dejsonfy_basic(self):
        self.assertEqual("aaa", IOUtils.dejsonfy("aaa"))
        self.assertEqual(42, IOUtils.dejsonfy(42))
        self.assertEqual(1.111, IOUtils.dejsonfy(1.111))
        self.assertEqual([1, 2.0, "ccc"], IOUtils.dejsonfy([1, 2.0, "ccc"]))
        self.assertEqual({"f1": 1, "f2": 2.0, "f3": "ccc"}, IOUtils.dejsonfy({"f1": 1, "f2": 2.0, "f3": "ccc"}))
        return

    ### Jsonfy & Dejsonfy X RecordClass

    class ExampleRecordClass(RecordClass):
        field_str: str
        field_int: int
        field_list: List[int]

    def test_jsonfy_record_class(self):
        example_obj = test_IOUtils.ExampleRecordClass(field_str="aaa", field_int=42, field_list=[1,2])
        jsonfied = IOUtils.jsonfy(example_obj)
        self.assertTrue(jsonfied.get("field_str") == "aaa")
        self.assertTrue(jsonfied.get("field_int") == 42)
        self.assertTrue(jsonfied.get("field_list") == [1,2])
        return

    def test_dejsonfy_record_class(self):
        example_obj = test_IOUtils.ExampleRecordClass(field_str="aaa", field_int=42, field_list=[1,2])
        dejsonfied = IOUtils.dejsonfy({"field_str": "aaa", "field_int": 42, "field_list": [1, 2]}, test_IOUtils.ExampleRecordClass)
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


if __name__ == '__main__':
    unittest.main()
