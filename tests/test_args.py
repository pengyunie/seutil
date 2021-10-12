import unittest

import seutil as su


class test_args(unittest.TestCase):

    def test_as_bool(self):
        self.assertEquals(su.args.Arg(None).bool_, True)
        self.assertEquals(su.args.Arg("T").bool_, True)
        self.assertEquals(su.args.Arg("t").bool_, True)
        self.assertEquals(su.args.Arg("true").bool_, True)
        self.assertEquals(su.args.Arg("True").bool_, True)
        self.assertEquals(su.args.Arg("F").bool_, False)
        self.assertEquals(su.args.Arg("f").bool_, False)
        self.assertEquals(su.args.Arg("false").bool_, False)
        self.assertEquals(su.args.Arg("False").bool_, False)
        with self.assertRaises(TypeError):
            su.args.Arg("123").as_bool()
        with self.assertRaises(TypeError):
            su.args.Arg(["123", "456"]).as_bool()

    def test_as_str(self):
        self.assertEquals(su.args.Arg("abcde").str_, "abcde")
        with self.assertRaises(TypeError):
            su.args.Arg(None).as_str()
        with self.assertRaises(TypeError):
            su.args.Arg(["123", "456"]).as_str()

    def test_as_int(self):
        self.assertEquals(su.args.Arg("53").int_, 53)
        with self.assertRaises(TypeError):
            su.args.Arg(None).as_int()
        with self.assertRaises(TypeError):
            su.args.Arg("33.44").as_int()
        with self.assertRaises(TypeError):
            su.args.Arg(["123", "456"]).as_int()

    def test_as_float(self):
        self.assertEquals(su.args.Arg("53").float_, 53)
        self.assertEquals(su.args.Arg("33.44").float_, 33.44)
        with self.assertRaises(TypeError):
            su.args.Arg(None).as_float()
        with self.assertRaises(TypeError):
            su.args.Arg("vvvvv").as_float()
        with self.assertRaises(TypeError):
            su.args.Arg(["123", "456"]).as_float()

    def test_as_list(self):
        self.assertEquals(su.args.Arg("53").list_, [53])
        self.assertEquals(su.args.Arg(["53", "33.44"]).list_, [53, 33.44])
        self.assertEquals(su.args.Arg(["53", "33.44"]).as_list(str), ["53", "33.44"])
        self.assertEquals(su.args.Arg(None).list_, [])

    def test_as_auto(self):
        self.assertEquals(su.args.Arg(None).auto_, None)
        self.assertEquals(su.args.Arg("true").auto_, True)
        self.assertEquals(su.args.Arg("True").auto_, True)
        self.assertEquals(su.args.Arg("false").auto_, False)
        self.assertEquals(su.args.Arg("False").auto_, False)
        self.assertEquals(su.args.Arg("1983").auto_, 1983)
        self.assertEquals(su.args.Arg("2202.3").auto_, 2202.3)
        self.assertEquals(su.args.Arg("98k").auto_, "98k")
        self.assertEquals(su.args.Arg(["53", "33.44"]).auto_, [53, 33.44])

    def test_args_get(self):
        args = su.args.Args(
            free=[su.args.Arg("34"), su.args.Arg("56.7"), su.args.Arg("ccc")],
            named={
                "opt1": su.args.Arg(["1", "2", "3"]),
                "color": su.args.Arg("red"),
                "yes": su.args.Arg(None),
            },
        )

        self.assertEquals(args[0].auto_, 34)
        self.assertEquals(args[1].auto_, 56.7)
        self.assertEquals(args[2].auto_, "ccc")
        self.assertEquals(args.get(0).auto_, 34)
        self.assertEquals(args.get(100).auto_, None)

        self.assertEquals(args["opt1"].auto_, [1, 2, 3])
        self.assertEquals(args["color"].auto_, "red")
        self.assertEquals(args["yes"].bool_, True)
        self.assertEquals(args["yes"].auto_, None)

    def test_args_misc(self):
        args = su.args.Args(
            free=[su.args.Arg("34"), su.args.Arg("56.7"), su.args.Arg("ccc")],
            named={
                "opt1": su.args.Arg(["1", "2", "3"]),
                "color": su.args.Arg("red"),
                "yes": su.args.Arg(None),
            },
        )

        self.assertEquals(len(args), 6)
        print(args)


class test_args_parse(unittest.TestCase):

    def test_sep_ws(self):
        args1 = su.args.parse(
            argv="-a 1 -b 2 --color red".split(),
            allow_sep_ws=True,
        )
        self.assertEquals(len(args1.free), 0)
        self.assertEquals(args1["a"].auto_, 1)
        self.assertEquals(args1["b"].auto_, 2)
        self.assertEquals(args1["color"].auto_, "red")

        args2 = su.args.parse(
            argv="-a 1 -b 2 --color red".split(),
            allow_sep_ws=False,
        )
        self.assertEquals(len(args2.free), 3)

    def test_sep_equal(self):
        args1 = su.args.parse(
            argv="-a=1 -b=2 --color=red".split(),
            allow_sep_equal=True,
        )
        self.assertEquals(len(args1.free), 0)
        self.assertEquals(args1["a"].auto_, 1)
        self.assertEquals(args1["b"].auto_, 2)
        self.assertEquals(args1["color"].auto_, "red")

        args2 = su.args.parse(
            argv="-a=1 -b=2 --color=red".split(),
            allow_sep_equal=False,
        )
        self.assertSetEqual(set(args2.named.keys()), {"a=1", "b=2", "color=red"})

    def test_gather_nargs(self):
        args1 = su.args.parse(
            argv="--nargs 1 2 3 4 -other=5".split(),
            allow_sep_ws=True,
            gather_nargs=True,
        )
        self.assertEquals(len(args1.free), 0)
        self.assertEquals(args1["nargs"].auto_, [1, 2, 3, 4])
        self.assertEquals(args1["other"].auto_, 5)

        args2 = su.args.parse(
            argv="--nargs 1 2 3 4 -other=5".split(),
            allow_sep_ws=True,
            gather_nargs=False,
        )
        self.assertEquals(len(args2.free), 3)
        self.assertEquals(args2["nargs"].auto_, 1)

    def test_multi_args(self):
        args1 = su.args.parse(
            argv="-opt=1 -opt=2 -opt=3".split(),
            multi_args="gather",
        )
        self.assertEquals(args1["opt"].auto_, [1, 2, 3])

        args2 = su.args.parse(
            argv="-opt=1 -opt=2 -opt=3".split(),
            multi_args="first",
        )
        self.assertEquals(args2["opt"].auto_, 1)

        args3 = su.args.parse(
            argv="-opt=1 -opt=2 -opt=3".split(),
            multi_args="last",
        )
        self.assertEquals(args3["opt"].auto_, 3)

    def test_free_args(self):
        args1 = su.args.parse("action -a 1".split())
        self.assertEquals(args1[0].auto_, "action")
        self.assertEquals(args1["a"].auto_, 1)
