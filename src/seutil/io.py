import bz2
import collections
import csv
import dataclasses
import enum
import gzip
import inspect
import io
import json
import lzma
import os
import pickle as pkl
import pydoc
import shutil
import tempfile
import warnings
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Optional,
    OrderedDict,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

import typing_inspect
import yaml

__all__ = [
    "cd",
    "rmdir",
    "rm",
    "mkdir",
    "mktmp",
    "mktmp_dir",
    "fmts",
    "Fmt",
    "serialize",
    "deserialize",
    "load",
    "dump",
    "DeserializationError",
    "InfoLossWarning",
]


class InfoLossWarning(Warning):
    """To indicate that some information could be lost during i/o operation"""

    pass


# ==========
# private utility functions
# ==========


def _unify_path(path: Union[str, Path]) -> Path:
    if not isinstance(path, Path):
        path = Path(path)
    return path


def _is_obj_named_tuple(obj: Any) -> bool:
    return obj is not None and isinstance(obj, tuple) and hasattr(obj, "_fields")


def _is_clz_named_tuple(clz: Type) -> bool:
    return clz is not None and inspect.isclass(clz) and issubclass(clz, tuple) and hasattr(clz, "_fields")


# ==========
# file and directory manipulation (creation/removal/browsing)
# ==========


class cd:
    """
    Temporally changes directory, for use with `with`:

    ```
    with cd(path):
        # cwd moved to path
        <statements>
    # cwd moved back to original cwd
    ```
    """

    def __init__(self, path: Union[str, Path]):
        path = _unify_path(path)
        self.path = path  # Path
        self.old_path = Path.cwd()  # Path

    def __enter__(self):
        os.chdir(self.path)

    def __exit__(self, type, value, tb):
        os.chdir(self.old_path)


def rmdir(
    path: Union[str, Path],
    missing_ok: bool = True,
    force: bool = True,
):
    """
    Removes a directory.

    :param path: the name of the directory.
    :param missing_ok: (-f) ignores error if the directory does not exist.
    :param force: (-f) force remove the directory even it's non-empty.
    """
    path = _unify_path(path)
    if path.is_dir():
        if force:
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.rmdir()
    else:
        if path.exists():
            raise OSError(f"Use rm to remove regular file {path}")
        else:
            if missing_ok:
                return
            else:
                raise FileNotFoundError(f"Cannot remove non-exist directory {path}")


def rm(
    path: Union[str, Path],
    missing_ok: bool = True,
    force: bool = True,
):
    """
    Removes a file/directory.

    :param path: the name of the file/directory.
    :param missing_ok: (-f) ignores error if the file/directory does not exist.
    :param force: (-rf) force remove the directory even it's not empty.
    """
    path = _unify_path(path)
    if path.is_dir():
        rmdir(path, missing_ok=missing_ok, force=force)
    elif path.exists():
        path.unlink(missing_ok=missing_ok)
    else:
        if not missing_ok:
            raise FileNotFoundError(f"Cannot remove non-exist file {path}")


def mkdir(
    path: Union[str, Path],
    parents: bool = True,
    fresh: bool = False,
):
    """
    Creates a directory.

    :param path: the path to the directory.
    :param parents: if True, automatically creates parent directories; otherwise, raise error if any parent is missing.
    :param fresh: if True and if the directory already exists, removes it before creating.
    """
    path = _unify_path(path)

    if path.exists() and fresh:
        rmdir(path)

    path.mkdir(parents=parents, exist_ok=not fresh)


def mktmp(
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    separator: str = "-",
    dir: Optional[Path] = None,
) -> Path:
    """
    Makes a temp file.  A wrapper for `tempfile.mkstemp`.
    """
    if prefix is not None:
        prefix = prefix + separator
    if suffix is not None:
        suffix = separator + suffix
    _, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir)
    return Path(path)


def mktmp_dir(
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    separator: str = "-",
    dir: Optional[Path] = None,
) -> Path:
    """
    Makes a temp directory.  A wrapper for `tempfile.mkdtemp`.
    """
    if prefix is not None:
        prefix = prefix + separator
    if suffix is not None:
        suffix = separator + suffix
    path = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=dir)
    return Path(path)


# ==========
# object (de)serialization
# ==========


# object before serialization
TObj = TypeVar("TObj")
# data after serialization, usually contain only primitive types and simple list and dict structures, that can be directly stored to disk
TData = TypeVar("TData")
# the target of deserialization, either a type or a type hint
TType = TypeVar("TType")
# the serializer callable: f(obj) -> data
TSerializer = Callable[[TObj], TData]
# the deserializer callable: f(data) -> obj OR f(data, type) -> obj
TDeserializer = Union[Callable[[TData], TObj], Callable[[TData, TType], TObj]]


_NON_TYPE = type(None)


class isobj_predefined(enum.Enum):
    type_eq = enum.auto()
    isinstance = enum.auto()


class isclz_predefined(enum.Enum):
    eq = enum.auto()
    issubclass = enum.auto()


@dataclasses.dataclass(frozen=True)
class TypeAdapter:
    isobj: Callable[[Any], bool]
    isclz: Callable[[Type], bool]
    serializer: Optional[TSerializer] = None
    deserializer: Optional[TDeserializer] = None
    deserializer_2args: bool = dataclasses.field(default=False, init=False)

    def __post_init__(self):
        if self.deserializer is not None and inspect.isfunction(self.deserializer):
            deserializer_sign = inspect.signature(self.deserializer)
            object.__setattr__(self, "deserializer_2args", len(deserializer_sign.parameters) >= 2)

    @classmethod
    def for_clz(
        cls,
        clz: Type,
        isobj: Union[isobj_predefined, Callable[[Any], bool]] = isobj_predefined.isinstance,
        isclz: Union[isclz_predefined, Callable[[Type], bool]] = isclz_predefined.issubclass,
        serializer: Optional[TSerializer] = None,
        deserializer: Optional[TDeserializer] = None,
    ) -> "TypeAdapter":
        """
        Creates a type adapter for a type with predefined isobj and isclz checkers.
        :param clz: the type to adapt.
        :param isobj: the isobj checker, can use one of isobj_predefined:
            * type_eq: check if the object strictly matches the given type.
            * isinstance (default): check if the object is an instance of the given type.
            Or, can use a custom checker, which takes an object and returns a bool.
        :param isclz: the isclz checker, can use one of isclz_predefined:
            * eq: check if the type strictly matches the given type.
            * issubclass (default): check if the type is a subclass of the given type.
            Or, can use a custom checker, which takes a type and returns a bool.
        :param serializer: the serializer, can be None if only registering a deserializer.
        :param deserializer: the deserializer, can be None if only registering a serializer.
        :return: the type adapter.
        """
        if isinstance(isobj, isobj_predefined):
            if isobj == isobj_predefined.type_eq:

                def isobj(x):
                    return type(x) == clz

            elif isobj == isobj_predefined.isinstance:

                def isobj(x):
                    return isinstance(x, clz)

        elif isobj is None:
            raise ValueError("isobj cannot be None")

        if isinstance(isclz, isclz_predefined):
            if isclz == isclz_predefined.eq:

                def isclz(x):
                    return x == clz

            elif isclz == isclz_predefined.issubclass:

                def isclz(x):
                    return inspect.isclass(x) and issubclass(x, clz)

        elif isclz is None:
            raise ValueError("isclz cannot be None")

        return cls(isobj=isobj, isclz=isclz, serializer=serializer, deserializer=deserializer)


_ADAPTERS: OrderedDict[Any, TypeAdapter] = collections.OrderedDict()


def has_adapter(key: Any) -> bool:
    """
    Checks if a type adapter is registered for the given key.
    :param key: the key of the type adapter.
    :return: if a type adapter is registered for the given key.
    """
    return key in _ADAPTERS


def set_adapter(key: Any, adapter: TypeAdapter, replace_existing: bool = True) -> None:
    """
    Registers a type adapter for the given key.
    :param key: the key of the type adapter.
    :param adapter: the type adapter.
    :param replace_existing: if True, replace the existing type adapter if any;
        otherwise, do not try to change the existing type adapter.
    :raises KeyError: if a type adapter for the given key already exists and replace_existing is False.
    """
    if key in _ADAPTERS and not replace_existing:
        raise KeyError(f"TypeAdapter for {key} already exists")
    _ADAPTERS[key] = adapter


def set_adapter_simple(
    clz: Type,
    serializer: Optional[Callable[[TObj], TData]] = None,
    deserializer: Optional[Callable[[TData, Type], TObj]] = None,
    replace_existing: bool = True,
) -> None:
    """
    Registers a type adapter for the given class, using it as the key, and with the given serializer & deserializer.
    :param clz: the class to set type adapter for.
    :param serializer: the serializer, can be None if only registering a deserializer.
    :param deserializer: the deserializer, can be None if only registering a serializer.
    :param replace_existing: if True, replace the existing type adapter if any;
    """
    set_adapter(
        clz,
        TypeAdapter.for_clz(clz, serializer=serializer, deserializer=deserializer),
        replace_existing=replace_existing,
    )


def unset_adapter(key: Any) -> None:
    """
    Unregisters a type adapter for the given key.
    :param key: the key of the type adapter.
    """
    if key in _ADAPTERS:
        del _ADAPTERS[key]


def rank_first_adapter(key: Any) -> None:
    """
    Moves the type adapter for the given key to the first position.
    :param key: the key of the type adapter.
    """
    _ADAPTERS.move_to_end(key, last=False)


def rank_last_adapter(key: Any) -> None:
    """
    Moves the type adapter for the given key to the last position.
    :param key: the key of the type adapter.
    """
    _ADAPTERS.move_to_end(key, last=True)


def serialize(
    obj: TObj,
    fmt: Optional["Formatter"] = None,
) -> TData:
    """
    Serializes an object into a data structure with only primitive types, list, dict.
    If fmt is provided, its formatting constraints are taken into account. Supported fmts:
    * json, jsonPretty, jsonNoSort, jsonList: dict only have str keys.
    TODO: move this considering of formatting constraints to a separate function, and let it automatically happen during dump; probably also add a reverse function which happens during load.

    :param obj: the object to be serialized.
    :param fmt: (optional) the target format.
    :return: the serialized object.
    """
    # Examine the type of object and use the appropriate serialization method
    # Check for simple types first
    if obj is None:
        return None
    elif isinstance(obj, (int, float, str, bool)):
        # Primitive types: keep as-is
        return obj
    elif hasattr(obj, "serialize"):
        # Call customized serialization method if exists
        return getattr(obj, "serialize")()
    elif _is_obj_named_tuple(obj):
        # NamedTuple
        return {k: serialize(v, fmt) for k, v in obj._asdict().items()}
    elif dataclasses.is_dataclass(obj):
        # Dataclass
        return {f.name: serialize(getattr(obj, f.name), fmt) for f in dataclasses.fields(obj)}
    elif isinstance(obj, (list, set, tuple)):
        # List-like: uniform to list; recursively serialize content
        return [serialize(item, fmt) for item in obj]
    elif isinstance(obj, dict):
        # Dict: recursively serialize content
        ret = {serialize(k, fmt): serialize(v, fmt) for k, v in obj.items()}

        # Json-like formats constraint: dict key must be str
        if fmt in [fmts.json, fmts.jsonPretty, fmts.jsonNoSort, fmts.jsonList]:
            ret = {str(k): v for k, v in ret.items()}
        return ret
    elif isinstance(obj, Enum):
        # Enum: use name
        return serialize(obj.name, fmt)
    else:
        # find in all registered type adapters
        for _, adapter in _ADAPTERS.items():
            if adapter.isobj(obj) and adapter.serializer is not None:
                return adapter.serializer(obj)

        # no serializer found
        raise TypeError(f"Cannot serialize object of type {type(obj)}, please consider writing a serialize() function")


class DeserializationError(RuntimeError):
    def __init__(self, data: TData, clz: Optional[Union[Type, str]], reason: str):
        self.data = data
        self.clz = clz
        self.reason = reason

    def __str__(self):
        return f"Cannot deserialize the following data to {self.clz}: {self.reason}\n  {self.data}"


def deserialize(
    data: TObj,
    clz: Optional[Union[Type, str]] = None,
    error: str = "ignore",
) -> TData:
    """
    Deserializes some data (with only primitive types, list, dict) to an object with
    proper types.

    :param data: the data to be deserialized.
    :param clz: the targeted type of deserialization (or its name); if None, will return
        the data as-is.
    :param error: what to do when the deserialization has problem:
        * raise: raise a DeserializationError.
        * ignore (default): return the data as-is.
    :return: the deserialized data.
    """
    if clz is None:
        return data

    assert error in ["raise", "ignore"]

    # Resolve type by name
    # TODO: cannot resolve generic types
    if isinstance(clz, str):
        clz = pydoc.locate(clz)

    # NoneType
    if clz == _NON_TYPE:
        if data is None:
            return data
        else:
            raise DeserializationError(data, clz, "None type received non-None data")

    clz_origin = typing_inspect.get_origin(clz)
    if clz_origin is None:
        clz_origin = clz
        generic = False
    else:
        generic = True
    clz_args = typing_inspect.get_args(clz)

    # print(f"deserialize({data=}, {clz=}, {error=}), {clz_origin=}, {clz_args=}")

    # Optional type: extract inner type
    if typing_inspect.is_optional_type(clz):
        if data is None:
            return None
        inner_clz = clz_args[0]
        try:
            return deserialize(data, inner_clz, error=error)
        except DeserializationError as e:
            raise DeserializationError(data, clz, f"(Optional removed) " + e.reason)

    # Union type: try each inner type
    if typing_inspect.is_union_type(clz):
        ret = None
        for inner_clz in clz_args:
            try:
                ret = deserialize(data, inner_clz, error="raise")
            except DeserializationError:
                continue

        if ret is None:
            if error == "raise":
                raise DeserializationError(data, clz, "All inner types are incompatible")
            else:
                return data
        else:
            return ret

    # None data, but not NoneType
    if data is None:
        if error == "raise":
            raise DeserializationError(data, clz, "None data for non-None type")
        else:
            return data

    # Find in all registered type adapters
    for _, adapter in _ADAPTERS.items():
        if adapter.isclz(clz) and adapter.deserializer is not None:
            if adapter.deserializer_2args:
                return adapter.deserializer(data, clz)
            else:
                return adapter.deserializer(data)

    # List-like types
    if clz_origin in [list, tuple, set, collections.deque, frozenset]:
        if not isinstance(data, list):
            if error == "raise":
                raise DeserializationError(data, clz, "Data does not have list structure")
            else:
                return data

        if clz_origin == tuple:
            # Unpack list to tuple
            return tuple(
                [
                    # If the list has more items than Tuple[xxx] declared (e.g., [1, 2, 3], Tuple[int]), repeat the last declared type
                    deserialize(
                        x,
                        clz_args[min(i, len(clz_args) - 1)] if generic else None,
                        error=error,
                    )
                    for i, x in enumerate(data)
                ]
            )
        else:
            # Unpack list
            ret = [deserialize(x, clz_args[0] if generic else None, error=error) for x in data]

            if clz_origin != list:
                # Convert to appropriate type
                return clz_origin(ret)
            else:
                return ret

    # Dict-like types
    if clz_origin in [
        dict,
        collections.OrderedDict,
        collections.defaultdict,
        collections.Counter,
    ]:
        if not isinstance(data, dict):
            if error == "raise":
                raise DeserializationError(data, clz, "Data does not have dict structure")
            else:
                return data

        if clz_origin == collections.OrderedDict:
            warnings.warn(
                f"The order of items in OrderedDict may not be preserved during deserialization",
                InfoLossWarning,
            )

        # Unpack dict
        ret = {
            deserialize(k, clz_args[0] if generic else None, error=error): deserialize(
                v, clz_args[1] if generic else None, error=error
            )
            for k, v in data.items()
        }
        if clz_origin != dict:
            # Convert to appropriate type
            obj_origin = clz_origin()
            obj_origin.update(ret)
            return obj_origin
        else:
            return ret

    # Use customized deserialize function, if exists
    if inspect.isclass(clz) and hasattr(clz, "deserialize"):
        # TODO: check parameter of the deserialize function
        return getattr(clz, "deserialize")(data)

    # Enum
    if inspect.isclass(clz) and issubclass(clz, Enum):
        if isinstance(data, str):
            return clz[data]
        else:
            if error == "raise":
                raise DeserializationError(data, clz, "Enum data must be str (name)")
            else:
                return data

    # NamedTuple
    if _is_clz_named_tuple(clz):
        field_values = {}
        for f in clz._fields:
            if hasattr(clz, "_field_types"):
                # for Python <3.9
                t = clz._field_types.get(f)
            elif hasattr(clz, "__annotations__"):
                # for Python >=3.9
                t = clz.__annotations__.get(f)
            else:
                t = None
            if f in data:
                field_values[f] = deserialize(data.get(f), t, error=error)
        return clz(**field_values)

    # DataClass
    if dataclasses.is_dataclass(clz):
        init_field_values = {}
        non_init_field_values = {}
        for f in dataclasses.fields(clz):
            if f.name in data:
                field_values = init_field_values if f.init else non_init_field_values
                field_values[f.name] = deserialize(data.get(f.name), f.type, error=error)
        obj = clz(**init_field_values)
        for f_name, f_value in non_init_field_values.items():
            # use object.__setattr__ in case clz is frozen
            object.__setattr__(obj, f_name, f_value)
        return obj

    # Primitive types
    if clz_origin == type(data):
        return data
    if clz_origin == float and type(data) == int:
        return data

    if error == "raise":
        raise DeserializationError(
            data,
            clz,
            f"Cannot match requested type ({clz} / {clz_origin}) with data's type ({type(data)})",
        )
    else:
        return data


# register (de)serializers for some popular 3rd party libraries

try:
    import numpy as np

    set_adapter_simple(
        np.ndarray,
        serializer=lambda x: serialize(x.tolist()),
        deserializer=lambda x: np.array(x),
    )

    # integers
    set_adapter_simple(np.byte, serializer=np.byte.item, deserializer=np.byte)
    set_adapter_simple(np.short, serializer=np.short.item, deserializer=np.short)
    set_adapter_simple(np.intc, serializer=np.intc.item, deserializer=np.intc)
    set_adapter_simple(np.int_, serializer=np.int_.item, deserializer=np.int_)
    set_adapter_simple(np.longlong, serializer=np.longlong.item, deserializer=np.longlong)

    # unsigned integers
    set_adapter_simple(np.ubyte, serializer=np.ubyte.item, deserializer=np.ubyte)
    set_adapter_simple(np.ushort, serializer=np.ushort.item, deserializer=np.ushort)
    set_adapter_simple(np.uintc, serializer=np.uintc.item, deserializer=np.uintc)
    set_adapter_simple(np.uint, serializer=np.uint.item, deserializer=np.uint)
    set_adapter_simple(np.ulonglong, serializer=np.ulonglong.item, deserializer=np.ulonglong)

    # floats
    set_adapter_simple(np.half, serializer=np.half.item, deserializer=np.half)
    set_adapter_simple(np.single, serializer=np.single.item, deserializer=np.single)
    set_adapter_simple(np.double, serializer=np.double.item, deserializer=np.double)
    set_adapter_simple(np.longdouble, serializer=np.longdouble.item, deserializer=np.longdouble)

    # other scalars
    set_adapter_simple(np.bool_, serializer=np.bool_.item, deserializer=np.bool_)
    # TODO: np.datetime64, np.timedelta64, np.object_, np.bytes_, np.str_, np.void, etc.
except ImportError:
    pass


try:
    import pandas as pd

    # series
    set_adapter_simple(pd.Series, serializer=lambda x: serialize(x.to_dict()), deserializer=pd.Series)

    # dataframe
    set_adapter_simple(
        pd.DataFrame,
        serializer=lambda x: serialize(x.to_dict(orient="records")),
        deserializer=pd.DataFrame.from_records,
    )
except ImportError:
    pass


try:
    import torch

    # tensor
    set_adapter_simple(
        torch.Tensor,
        serializer=lambda x: serialize(x.tolist()),
        deserializer=torch.tensor,
    )
except ImportError:
    pass


try:
    import recordclass

    def _is_obj_record_class(obj: Any) -> bool:
        return obj is not None and isinstance(obj, recordclass.mutabletuple) or isinstance(obj, recordclass.dataobject)

    def _is_clz_record_class(clz: Type) -> bool:
        return (
            clz is not None
            and inspect.isclass(clz)
            and (issubclass(clz, recordclass.mutabletuple) or issubclass(clz, recordclass.dataobject))
        )

    def _serialize_recordclass(obj) -> dict:
        warnings.warn(
            "The support for recordclass may be dropped in the future. Please consider using dataclass instead.",
            DeprecationWarning,
        )
        if hasattr(obj, "__dict__"):
            # Older versions of recordclass
            return {k: serialize(v) for k, v in obj.__dict__.items()}
        else:
            # Newer versions of recordclass
            return {f: serialize(getattr(obj, f)) for f in obj.__fields__}

    def _deseralize_recordclass(data, clz) -> Any:
        warnings.warn(
            "The support for recordclass may be dropped in the future. Please consider using dataclass instead.",
            DeprecationWarning,
        )
        field_values = {}
        for f, t in get_type_hints(clz).items():
            if f in data:
                # TODO: the error parameter is lost
                field_values[f] = deserialize(data.get(f), t)
        return clz(**field_values)

    set_adapter(
        recordclass.RecordClass,
        TypeAdapter(
            isobj=_is_obj_record_class,
            isclz=_is_clz_record_class,
            serializer=_serialize_recordclass,
            deserializer=_deseralize_recordclass,
        ),
    )

except ImportError:
    pass


# ==========
# file read and write
# ==========


@dataclasses.dataclass(frozen=True)
class Formatter:
    # The function used by dump
    # * line_mode=False:  takes a file-object and obj as input, writes the obj to the file-object
    # * line_mode=True:  takes an item in the obj as input (from for loop), returns one line of text *without* "\n"
    writer: Union[Callable[[io.IOBase, Any], None], Callable[[Any], str]]

    # The function used by load
    # * line_mode=False:  takes a file-object as input, reads the entire file and returns the obtained obj
    # * line_mode=True:  takes one line of text as input, returns the obtained obj
    reader: Union[Callable[[io.IOBase], Any], Callable[[str], Any]]

    # File extensions, used for format inference; the first extension is used for output
    exts: Optional[List[str]] = None

    # If the file should be opened in binary mode
    binary: bool = False

    # If the file should be read/written one line at a time
    line_mode: bool = False

    # If this format requires (de)serialization
    serialize: bool = False


class fmts:
    # === txt ===
    txt = Formatter(
        writer=lambda f, obj: f.write(str(obj)),
        reader=lambda f: f.read(),
        exts=["txt"],
    )

    # === pickle ===
    pickle = Formatter(
        writer=lambda f, obj: pkl.dump(obj, f),
        reader=lambda f: pkl.load(f),
        exts=["pkl", "pickle"],
        binary=True,
    )

    # === json ===
    json = Formatter(
        writer=lambda f, obj: json.dump(obj, f, sort_keys=True),
        reader=lambda f: json.load(f),
        exts=["json"],
        serialize=True,
    )
    # Use yaml loader to allow formatting errors (e.g., trailing commas), but cannot handle unprintable chars
    jsonFlexible = dataclasses.replace(json, reader=lambda f: yaml.load(f, Loader=yaml.FullLoader))
    json_flexible = jsonFlexible
    # Pretty-print version with sorting keys
    jsonPretty = dataclasses.replace(json, writer=lambda f, obj: json.dump(obj, f, sort_keys=True, indent=4))
    json_pretty = jsonPretty
    # Pretty-print version without sorting keys
    jsonNoSort = dataclasses.replace(json, writer=lambda f, obj: json.dump(obj, f, indent=4))
    json_no_sort = jsonNoSort

    # === jsonl (json list) ===
    jsonList = Formatter(
        writer=lambda item: json.dumps(item),
        reader=lambda line: json.loads(line),
        exts=["jsonl"],
        line_mode=True,
        serialize=True,
    )
    json_list = jsonList

    # === text list ===
    txtList = Formatter(
        writer=lambda item: str(item),
        reader=lambda line: line.replace("\n", ""),
        exts=["txt"],
        line_mode=True,
    )
    txt_list = txtList

    # === yaml ===
    yaml = Formatter(
        writer=lambda f, obj: yaml.dump(obj, f),
        reader=lambda f: yaml.load(f, Loader=yaml.FullLoader),
        exts=["yml", "yaml"],
        serialize=True,
    )

    # === csv list ===
    csvList = Formatter(
        # TODO: add a checker to ensure the input is list of list
        writer=lambda f, obj: csv.writer(f).writerows(obj),
        reader=lambda f: "".join([",".join(row) for row in csv.reader(f)]),
        exts=["csv"],
        serialize=True,
    )
    csv_list = csvList

    all_fmts = [v for v in locals().values() if isinstance(v, Formatter)]


# backward compatibility
Fmt = fmts


@dataclasses.dataclass(frozen=True)
class Compressor:
    # open function alternative to os.open
    open_fn: Callable

    # File extensions, used for format inference; the first extension is used for output
    exts: Optional[List[str]] = None


class compressors:
    # === gzip ===
    gzip = Compressor(open_fn=gzip.open)

    # === bz2 ===
    bz2 = Compressor(open_fn=bz2.open)

    # === lzma ===
    lzma = Compressor(open_fn=lzma.open)

    all_compressors = [v for v in locals().values() if isinstance(v, Compressor)]


def _infer_from_path(path: Path) -> Tuple[Formatter, Compressor]:
    name = path.name
    fmt = None
    compressor = None

    if "." not in name:
        return fmt, compressor
    name, ext = name.rsplit(".", 1)

    # detect possible compressor extension
    for x in compressors.all_compressors:
        if x.exts is not None and ext in x.exts:
            compressor = x

            # take the next extension
            if "." not in name:
                return fmt, compressor
            name, ext = name.rsplit(".", 1)

            break

    # detect possible format extension
    for x in fmts.all_fmts:
        if x.exts is not None and ext in x.exts:
            fmt = x
            break

    return fmt, compressor


def dump(
    path: Union[str, Path],
    obj: object,
    fmt: Optional[Formatter] = None,
    compressor: Optional[Compressor] = None,
    serialization: Optional[bool] = None,
    parents: bool = True,
    append: bool = False,
    exists_ok: bool = True,
    serialization_fmt_aware: bool = True,
) -> None:
    """
    Saves an object to a file.
    The format is automatically inferred from the file name, if not otherwise specified.
    By default, serialization (i.e., converting to primitive types and data structures) is
    automatically performed for the formats that needs it (e.g., json).

    :param path: the path to save the file.
    :param obj: the object to be saved.
    :param fmt: the format of the file; if None (default), inferred from path.
    :param compressor: the compression format of the file; if None (default), inferred from path.
    :param serialization: whether or not to serialize the object before saving:
        * True: always serialize;
        * None (default): only serialize for the formats that needs it;
        * False: never serialize.
    :param parents: what to do if parent directories of path do not exist:
        * True (default): automatically create them;
        * False: raise Exception.
    :param append: whether to append to an existing file if any (default False).
    :param exists_ok: what to do if path already exists and append is False:
        * True (default): automatically rewrites it;
        * False: raise Exception.
    :param serialization_fmt_aware: let the serialization function be aware of the target
        format to fit its constraints (e.g., dictionaries in json format can only have
        str keys).
    """
    path = _unify_path(path)

    # Check path existence
    if path.exists():
        if exists_ok:
            if not append:
                # make sure the existing file is removed in non-append mode
                rm(path)
        else:
            raise FileExistsError(str(path))

    # Create parent directories
    if not path.parent.is_dir():
        if parents:
            path.parent.mkdir(parents=True)
        else:
            raise FileNotFoundError(str(path.parent))

    # Infer format
    if fmt is None or compressor is None:
        inferred_fmt, inferred_compressor = _infer_from_path(path)
        if fmt is None:
            fmt = inferred_fmt
        if compressor is None:
            compressor = inferred_compressor

    if fmt is None:
        raise RuntimeError(f"Cannot infer format for file {path}")

    if append and not fmt.line_mode:
        raise RuntimeWarning(f"Cannot append to a non-list-like format ({fmt})")

    # Serialize (when appropriate)
    if serialization is None:
        serialization = fmt.serialize

    if serialization:
        obj = serialize(
            obj,
            fmt=fmt if serialization_fmt_aware else None,
        )

    # Open file
    file_mode = "w" if not append else "a"
    if fmt.binary:
        file_mode += "b"
    elif compressor is not None:
        file_mode += "t"

    open_fn = open if compressor is None else compressor.open_fn

    with open_fn(path, file_mode) as f:
        # Write content
        if not fmt.line_mode:
            fmt.writer(f, obj)
        else:
            for item in obj:
                # Removing all "\n" inside the line
                f.write(fmt.writer(item).replace("\n", " ") + "\n")


def load(
    path: Union[str, Path],
    fmt: Optional[Formatter] = None,
    compressor: Optional[Compressor] = None,
    serialization: Optional[bool] = None,
    clz: Optional[Type] = None,
    error: str = "ignore",
    iter_line: bool = False,
) -> Union[object, Iterator[object]]:
    """
    Loads an object from a file.
    The format is automatically inferred from the file name, if not otherwise specified.
    By default, if clz is given, deserialization (i.e., unpacking from primitive types
    and data structures) is automatically performed for the formats that needs it (e.g., json).

    :param path: the path to load the object.
    :param fmt: the format of the file; if None (default), inferred from path.
    :param compressor: the compression format of the file; if None (default), inferred from path.
    :param serialization: whether or not to deserialize the object after loading:
        * True: always serialize;
        * None (default): only serialize for the formats that needs it;
        * False: never serialize.
    :param clz: the class to use for deserialization; if None (default), deserialization is a no-op.
    :param error: what to do if deserialization fails:
        * raise: raise a DeserializationError.
        * ignore (default): return the data as-is.
    :param iter_line: whether to iterate over the lines of the file instead of loading the whole file.
    """
    path = _unify_path(path)

    # Infer format
    if fmt is None or compressor is None:
        inferred_fmt, inferred_compressor = _infer_from_path(path)
        if fmt is None:
            fmt = inferred_fmt
        if compressor is None:
            compressor = inferred_compressor

    if fmt is None:
        raise RuntimeError(f"Cannot infer format for file {path}")

    # Check arguments
    if iter_line and not fmt.line_mode:
        raise RuntimeWarning(f"Cannot iteratively load a non-list-like format ({fmt})")

    if serialization is None:
        serialization = fmt.serialize

    # Open file
    file_mode = "r"
    if fmt.binary:
        file_mode += "b"
    elif compressor is not None:
        file_mode += "t"

    open_fn = open if compressor is None else compressor.open_fn

    # Load content
    if not fmt.line_mode:
        with open_fn(path, file_mode) as f:
            obj = fmt.reader(f)
            if serialization:
                obj = deserialize(obj, clz, error=error)
            return obj
    else:
        iterator = LoadIterator(path, file_mode, open_fn, fmt, serialization, clz, error)
        if iter_line:
            return iterator
        else:
            return list(iterator)


class LoadIterator(Iterator):
    def __init__(
        self,
        path: Path,
        file_mode: str,
        open_fn: Callable,
        fmt: Formatter,
        serialization: bool,
        clz: Optional[Type],
        error: str = "ignore",
    ):
        self.fd = open_fn(path, file_mode)
        self.fmt = fmt
        self.serialization = serialization
        self.clz = clz
        self.error = error

    def __next__(self):
        line = self.fd.readline()
        if line == "":
            # EOF
            self.fd.close()
            raise StopIteration
        item = self.fmt.reader(line)
        if self.serialization:
            item = deserialize(item, self.clz, error=self.error)
        return item
