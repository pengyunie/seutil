import collections
import dataclasses
import inspect
import io
import json
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
    Dict,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

import recordclass
import typing_inspect
import yaml
import csv

__all__ = [
    "cd",
    "rmdir",
    "rm",
    "mkdir",
    "mktmp",
    "mktmp_dir",
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


def _is_obj_record_class(obj: Any) -> bool:
    return (
        obj is not None
        and isinstance(obj, recordclass.mutabletuple)
        or isinstance(obj, recordclass.dataobject)
    )


def _is_clz_record_class(clz: Type) -> bool:
    return (
        clz is not None
        and inspect.isclass(clz)
        and (
            issubclass(clz, recordclass.mutabletuple)
            or issubclass(clz, recordclass.dataobject)
        )
    )


def _is_obj_named_tuple(obj: Any) -> bool:
    return obj is not None and isinstance(obj, tuple) and hasattr(obj, "_fields")


def _is_clz_named_tuple(clz: Type) -> bool:
    return (
        clz is not None
        and inspect.isclass(clz)
        and issubclass(clz, tuple)
        and hasattr(clz, "_fields")
    )


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


_NON_TYPE = type(None)


_SERIALIZERS: Dict[type, Callable[[TObj], TData]] = {}
_DESERIALIZERS: Dict[type, Callable[[TData], TObj]] = {}


def register_type(
    clz: Type,
    serializer: Optional[Callable[[TObj], TData]] = None,
    deserializer: Optional[Callable[[TData], TObj]] = None,
    replace: bool = True,
) -> bool:
    """
    Register customized serializer and/or deserializer of a type.
    The registered (de)serializer is only good for this particular type and *not* for its subtypes.
    If an inheritable (de)serializer is desired, declare a method in the base class called `(de)serializer` instead.

    :param clz: the type to register.
    :param serializer: the serializer, can be None if only registering a deserializer.
    :param deserializer: the deserializer, can be None if only registering a serializer.
    :param replace: if True, replace the existing (de)serializer if any; otherwise, do not change the existing (de)serializer.
    :return: if any new (de)serializer is registered.
    """
    changed = False

    if serializer is not None:
        if clz in _SERIALIZERS and not replace:
            pass
        else:
            _SERIALIZERS[clz] = serializer
            changed = True
    if deserializer is not None:
        if clz in _DESERIALIZERS and not replace:
            pass
        else:
            _DESERIALIZERS[clz] = deserializer
            changed = True

    return changed


def unregister_type(
    clz: Type, serializer: bool = True, deserializer: bool = True
) -> bool:
    """
    Unregister customized serializer and/or deserializer of a type.
    Similar to register_type, the unregistering only happens for this particular type and *not* for its subtypes.

    :param clz: the type to unregister.
    :param serializer: if True (default), unregister the serializer.
    :param deserializer: if True (default), unregister the deserializer.
    :return: if any (de)serializer is unregistered.
    """
    changed = False
    if serializer:
        if clz in _SERIALIZERS:
            del _SERIALIZERS[clz]
            changed = True
    if deserializer:
        if clz in _DESERIALIZERS:
            del _DESERIALIZERS[clz]
            changed = True
    return changed


def serialize(
    obj: TObj,
    fmt: Optional["Fmt"] = None,
) -> TData:
    """
    Serializes an object into a data structure with only primitive types, list, dict.
    If fmt is provided, its formatting constraints are taken into account. Supported fmts:
    * json, jsonPretty, jsonNoSort, jsonList: dict only have str keys.
    TODO: move this considering of formatting constraints to a spearate function, and let it automatically happen during dump; probably also add a reverse function which happens during load.

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
        return {
            f.name: serialize(getattr(obj, f.name), fmt)
            for f in dataclasses.fields(obj)
        }
    elif isinstance(obj, (list, set, tuple)):
        # List-like: uniform to list; recursively serialize content
        return [serialize(item, fmt) for item in obj]
    elif isinstance(obj, dict):
        # Dict: recursively serialize content
        ret = {serialize(k, fmt): serialize(v, fmt) for k, v in obj.items()}

        # Json-like formats constraint: dict key must be str
        if fmt in [Fmt.json, Fmt.jsonPretty, Fmt.jsonNoSort, Fmt.jsonList]:
            ret = {str(k): v for k, v in ret.items()}
        return ret
    elif isinstance(obj, Enum):
        # Enum: use name
        return serialize(obj.name, fmt)
    elif _is_obj_record_class(obj):
        # RecordClass: convert to dict
        if hasattr(obj, "__dict__"):
            # Older versions of recordclass
            return {k: serialize(v, fmt) for k, v in obj.__dict__.items()}
        else:
            # Newer versions of recordclass
            return {f: serialize(getattr(obj, f), fmt) for f in obj.__fields__}
    elif type(obj) in _SERIALIZERS:
        # Use registered serializer if exists
        return _SERIALIZERS[type(obj)](obj)
    else:
        raise TypeError(
            f"Cannot serialize object of type {type(obj)}, please consider writing a serialize() function"
        )


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
                raise DeserializationError(
                    data, clz, "All inner types are incompatible"
                )
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

    # Use registered deserializer if exists
    if clz in _DESERIALIZERS:
        return _DESERIALIZERS[clz](data)

    # List-like types
    if clz_origin in [list, tuple, set, collections.deque, frozenset]:
        if not isinstance(data, list):
            if error == "raise":
                raise DeserializationError(
                    data, clz, "Data does not have list structure"
                )
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
            ret = [
                deserialize(x, clz_args[0] if generic else None, error=error)
                for x in data
            ]

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
                raise DeserializationError(
                    data, clz, "Data does not have dict structure"
                )
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

    # RecordClass
    if _is_clz_record_class(clz):
        field_values = {}
        for f, t in get_type_hints(clz).items():
            if f in data:
                field_values[f] = deserialize(data.get(f), t, error=error)
        return clz(**field_values)

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
                field_values[f.name] = deserialize(
                    data.get(f.name), f.type, error=error
                )
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

    register_type(
        np.ndarray,
        serializer=lambda x: serialize(x.tolist()),
        deserializer=lambda x: np.array(x),
    )

    # integers
    register_type(np.byte, serializer=np.byte.item, deserializer=np.byte)
    register_type(np.short, serializer=np.short.item, deserializer=np.short)
    register_type(np.intc, serializer=np.intc.item, deserializer=np.intc)
    register_type(np.int_, serializer=np.int_.item, deserializer=np.int_)
    register_type(np.longlong, serializer=np.longlong.item, deserializer=np.longlong)

    # unsigned integers
    register_type(np.ubyte, serializer=np.ubyte.item, deserializer=np.ubyte)
    register_type(np.ushort, serializer=np.ushort.item, deserializer=np.ushort)
    register_type(np.uintc, serializer=np.uintc.item, deserializer=np.uintc)
    register_type(np.uint, serializer=np.uint.item, deserializer=np.uint)
    register_type(np.ulonglong, serializer=np.ulonglong.item, deserializer=np.ulonglong)

    # floats
    register_type(np.half, serializer=np.half.item, deserializer=np.half)
    register_type(np.single, serializer=np.single.item, deserializer=np.single)
    register_type(np.double, serializer=np.double.item, deserializer=np.double)
    register_type(
        np.longdouble, serializer=np.longdouble.item, deserializer=np.longdouble
    )

    # other scalars
    register_type(np.bool_, serializer=np.bool_.item, deserializer=np.bool_)
    # TODO: np.datetime64, np.timedelta64, np.object_, np.bytes_, np.str_, np.void, etc.
except ImportError:
    pass


try:
    import pandas as pd

    # series
    register_type(
        pd.Series, serializer=lambda x: serialize(x.to_dict()), deserializer=pd.Series
    )

    # dataframe
    register_type(
        pd.DataFrame,
        serializer=lambda x: serialize(x.to_dict(orient="records")),
        deserializer=pd.DataFrame.from_records,
    )
except ImportError:
    pass


try:
    import torch

    # tensor
    register_type(
        torch.Tensor,
        serializer=lambda x: serialize(x.tolist()),
        deserializer=torch.tensor,
    )
except ImportError:
    pass


# ==========
# file read and write
# ==========


class FmtProperty(NamedTuple):
    # The function used by dump
    # * line_mode=False:  takes a file-object and obj as input, writes the obj to the file-object
    # * line_mode=True:  takes an item in the obj as input (from for loop), returns one line of text *without* "\n"
    writer: Union[Callable[[io.IOBase, Any], None], Callable[[Any], str]]

    # The function used by load
    # * line_mode=False:  takes a file-object as input, reads the entire file and returns the obtained obj
    # * line_mode=True:  takes one line of text as input, returns the obtained obj
    reader: Union[Callable[[io.IOBase], Any], Callable[[str], Any]]

    # File extensions, used for format inference; the first extension is used for output
    exts: List[str] = None

    # If the file should be opened in binary mode
    binary: bool = False

    # If the file should be read/writen one line at a time
    line_mode: bool = False

    # If this format requires (de)serialization
    serialize: bool = False


class Fmt(FmtProperty, Enum):
    # === txt ===
    txt = FmtProperty(
        writer=lambda f, obj: f.write(str(obj)),
        reader=lambda f: f.read(),
        exts=["txt"],
    )
    # === pickle ===
    pickle = FmtProperty(
        writer=lambda f, obj: pkl.dump(obj, f),
        reader=lambda f: pkl.load(f),
        exts=["pkl", "pickle"],
        binary=True,
    )
    # === json ===
    json = FmtProperty(
        writer=lambda f, obj: json.dump(obj, f, sort_keys=True),
        reader=lambda f: json.load(f),
        exts=["json"],
        serialize=True,
    )
    # Use yaml loader to allow formatting errors (e.g., trailing commas), but cannot handle unprintable chars
    jsonFlexible = json._replace(reader=lambda f: yaml.load(f, Loader=yaml.FullLoader))
    # Pretty-print version with sorting keys
    jsonPretty = json._replace(
        writer=lambda f, obj: json.dump(obj, f, sort_keys=True, indent=4),
    )
    # Pretty-print version without sorting keys
    jsonNoSort = json._replace(
        writer=lambda f, obj: json.dump(obj, f, indent=4),
    )
    # === jsonl (json list) ===
    jsonList = FmtProperty(
        writer=lambda item: json.dumps(item),
        reader=lambda line: json.loads(line),
        exts=["jsonl"],
        line_mode=True,
        serialize=True,
    )
    # === text list ===
    txtList = FmtProperty(
        writer=lambda item: str(item),
        reader=lambda line: line.replace("\n", ""),
        exts=["txt"],
        line_mode=True,
    )
    # === yaml ===
    yaml = FmtProperty(
        writer=lambda f, obj: yaml.dump(obj, f),
        reader=lambda f: yaml.load(f, Loader=yaml.FullLoader),
        exts=["yml", "yaml"],
        serialize=True,
    )
    # === csv list ===
    csvList = FmtProperty(
        writer=lambda f, obj: csv.writer(f).writerows(obj),
        reader=lambda f: "".join([",".join(row) for row in csv.reader(f)]),
        exts=["csv"],
        serialize=True,
    )


def infer_fmt_from_ext(ext: str, default: Optional[Fmt] = None) -> Fmt:
    if ext.startswith("."):
        ext = ext[1:]

    for fmt in Fmt:
        if fmt.exts is not None and ext in fmt.exts:
            return fmt

    if default is not None:
        return default
    else:
        raise RuntimeError(f'Cannot infer format for extension "{ext}"')


def dump(
    path: Union[str, Path],
    obj: object,
    fmt: Optional[Fmt] = None,
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
    if path.exists() and not exists_ok:
        raise FileExistsError(str(path))

    # Create parent directories
    if not path.parent.is_dir():
        if parents:
            path.parent.mkdir(parents=True)
        else:
            raise FileNotFoundError(str(path.parent))

    # Infer format
    if fmt is None:
        fmt = infer_fmt_from_ext(path.suffix)

    if append and not fmt.line_mode:
        raise RuntimeWarning(
            f"Appending to a format that's not list-like ({fmt}) may result in invalid file"
        )

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

    with open(path, file_mode) as f:
        # Write content
        if not fmt.line_mode:
            fmt.writer(f, obj)
        else:
            for item in obj:
                # Removing all "\n" inside the line
                f.write(fmt.writer(item).replace("\n", " ") + "\n")


def load(
    path: Union[str, Path],
    fmt: Optional[Fmt] = None,
    serialization: Optional[bool] = None,
    clz: Optional[Type] = None,
    error: str = "ignore",
    iter_line: bool = False,
) -> Union[object, Iterator[object]]:
    """
    Loads an object from a file.
    The format is automatically inferred from the file name, if not otherwise specified.
    By default, if clz is given, deserialization (i.e., unpackingn from primitive types
    and data structures) is automatically performed for the formats that needs it (e.g., json).

    :param path: the path to load the object.
    :param fmt: the format of the file; if None (default), inferred from path.
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
    if fmt is None:
        fmt = infer_fmt_from_ext(path.suffix)

    # Check arguments
    if iter_line and not fmt.line_mode:
        raise RuntimeError(f"Cannot load format {fmt} file under line mode")

    if serialization is None:
        serialization = fmt.serialize

    # Open file
    file_mode = "r"
    if fmt.binary:
        file_mode += "b"

    # Load content
    if not fmt.line_mode:
        with open(path, file_mode) as f:
            obj = fmt.reader(f)
            if serialization:
                obj = deserialize(obj, clz, error=error)
            return obj
    else:
        iterator = LoadIterator(path, file_mode, fmt, serialization, clz, error)
        if iter_line:
            return iterator
        else:
            return list(iterator)


class LoadIterator(Iterator):
    def __init__(
        self,
        path: Path,
        file_mode: str,
        fmt: FmtProperty,
        serialization: bool,
        clz: Optional[Type],
        error: str = "ignore",
    ):
        self.fd = open(path, file_mode)
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
