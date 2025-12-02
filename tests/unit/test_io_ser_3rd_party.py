import collections
import math
from typing import Dict, Optional

import pytest

from .test_io_ser import check_serialization_ok


class Test_io_ser_numpy:
    np = pytest.importorskip("numpy")

    def test_ser_array_int_1d(self):
        check_serialization_ok(
            obj=self.np.array([1, 2, 3]),
            data=[1, 2, 3],
            obj_eq=self.np.array_equal,
        )

    def test_ser_array_int_2d(self):
        check_serialization_ok(
            obj=self.np.array([[1, 2, 3], [4, 5, 6]]),
            data=[[1, 2, 3], [4, 5, 6]],
            obj_eq=self.np.array_equal,
        )

    def test_ser_array_float_1d(self):
        check_serialization_ok(
            obj=self.np.array([1.0, 2.3, 3.4]),
            data=[1.0, 2.3, 3.4],
            obj_eq=self.np.array_equal,
        )

    def test_ser_array_float_2d(self):
        check_serialization_ok(
            obj=self.np.array([[1.0, 2.3, 3.4], [4.5, 5.6, 6.7]]),
            data=[[1.0, 2.3, 3.4], [4.5, 5.6, 6.7]],
            obj_eq=self.np.array_equal,
        )

    @pytest.mark.parametrize(
        "obj",
        [
            # signed integers
            np.byte(1),
            np.int8(42),
            np.short(2),
            np.int16(32_742),
            np.intc(3),
            np.int32(2_147_483_642),
            np.int_(4),
            np.int64(9_223_372_036_854_775_742),
            np.longlong(9_223_372_036_854_775_742),
            # unsigned integers
            np.ubyte(1),
            np.uint8(242),
            np.ushort(2),
            np.uint16(65_442),
            np.uintc(3),
            np.uint32(4_294_967_242),
            np.uint(4),
            np.uint64(18_446_744_073_709_551_542),
            np.ulonglong(18_446_744_073_709_551_542),
        ],
    )
    def test_ser_scalar_integer(self, obj):
        check_serialization_ok(
            obj=obj,
            data=obj.item(),
        )

    @pytest.mark.parametrize(
        "obj",
        [
            np.half(1.0),
            np.float16(1.1),
            np.single(2.0),
            np.float32(2.1),
            np.double(3.0),
            np.float64(3.1),
        ],
    )
    def test_ser_scalar_float(self, obj):
        check_serialization_ok(
            obj=obj,
            data=obj.item(),
        )

    @pytest.mark.parametrize("obj", [np.bool_(True), np.bool_(False)])
    def test_ser_scalar_bool(self, obj):
        check_serialization_ok(
            obj=obj,
            data=obj.item(),
        )

    @pytest.mark.xfail(reason="complex types are not supported yet")
    @pytest.mark.parametrize(
        "obj",
        [
            np.csingle(1.0 + 1.0j),
            np.complex64(1.2 + 1.2j),
            np.cdouble(2.0 + 2.0j),
            np.complex128(2.3 + 2.3j),
        ],
    )
    def test_ser_scalar_complex_unsupported(self, obj):
        check_serialization_ok(
            obj=obj,
            data=obj.item(),
        )


class Test_io_ser_pandas:
    pd = pytest.importorskip("pandas")

    def test_ser_series(self):
        check_serialization_ok(
            obj=self.pd.Series([1, 2, 3]),
            data={0: 1, 1: 2, 2: 3},
            obj_eq=self.pd.Series.equals,
        )

    def test_ser_dataframe(self):
        check_serialization_ok(
            obj=self.pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
            data=[{"a": 1, "b": 4}, {"a": 2, "b": 5}, {"a": 3, "b": 6}],
            obj_eq=self.pd.DataFrame.equals,
        )


class Test_io_ser_pytorch:
    torch = pytest.importorskip("torch")

    def test_ser_tensor_scaler_long(self):
        check_serialization_ok(
            obj=self.torch.tensor(1),
            data=1,
            obj_eq=self.torch.equal,
        )

    def test_ser_tensor_scaler_float(self):
        check_serialization_ok(
            obj=self.torch.tensor(4.2),
            data=4.2,
            obj_eq=self.torch.equal,
            data_eq=lambda a, b: math.isclose(a, b, rel_tol=1e-7),
        )

    @pytest.mark.xfail(
        reason="types of tensors collapse to the default ones (long/float) after a serialization-deserialization loop"
    )
    def test_ser_tensor_not_serializing_type_long(self):
        check_serialization_ok(
            obj=self.torch.tensor(1, dtype=self.torch.int),
            data=1,
            obj_eq=self.torch.equal,
        )

    @pytest.mark.xfail(
        reason="types of tensors collapse to the default ones (long/float) after a serialization-deserialization loop"
    )
    def test_ser_tensor_not_serializing_type_float(self):
        check_serialization_ok(
            obj=self.torch.tensor(4.2, dtype=self.torch.double),
            data=4.2,
            obj_eq=self.torch.equal,
        )


class Test_io_ser_recordclass:
    recordclass = pytest.importorskip("recordclass")

    def test_ser_record_class(self):
        ExampleNamedTuple = collections.namedtuple("ExampleNamedTuple", ["e", "f", "g"])

        class ExampleRecordClass(self.recordclass.RecordClass):
            h: int
            i: float
            j: Dict[str, float] = None
            k: Optional[ExampleNamedTuple] = None

        with pytest.deprecated_call():
            check_serialization_ok(
                obj=ExampleRecordClass(h=4, i=0.5, j={"a": 4, "b": 6.0}, k=ExampleNamedTuple(99, [3, 5], 42.0)),
                data={
                    "h": 4,
                    "i": 0.5,
                    "j": {"a": 4, "b": 6.0},
                    "k": {"e": 99, "f": [3, 5], "g": 42.0},
                },
            )
