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
from enum import Enum
from pathlib import Path
from typing import *

import recordclass
import typing_inspect
import yaml

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
]


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
# multi-format dumping/loading with serialization
# ==========


class FmtProperty(NamedTuple):
    # The function used by dump
    # * list_like=False:  takes a file-object and obj as input, writes the obj to the file-object
    # * list_like=True:  takes an item in the obj as input (from for loop), returns one line of text *without* "\n"
    writer: Union[Callable[[io.IOBase, Any], None], Callable[[Any], str]]

    # The function used by load
    # * list_like=False:  takes a file-object as input, reads the entire file and returns the obtained obj
    # * list_like=True:  takes one line of text as input, returns the obtained obj
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
        # Use yaml loader to allow formatting errors (e.g., trailing commas)
        reader=lambda f: yaml.load(f, Loader=yaml.FullLoader),
        exts=["json"],
        serialize=True,
    )
    # Pretty-print version with sorting keys
    jsonPretty = json._replace(
        writer=lambda f, obj: json.dump(obj, f, sort_keys=True, indent=4),
    )
    # Pretty-print version without sorting keys
    jsonNoSort = json._replace(
        writer=lambda f, obj: json.dump(obj, f, indent=4),
    )
    # === jsonl === aka json list
    jsonList = FmtProperty(
        writer=lambda item: json.dumps(item),
        reader=lambda line: json.loads(line),
        exts=["jsonl"],
        line_mode=True,
        serialize=True,
    )
    txtList = FmtProperty(
        writer=lambda item: str(item),
        reader=lambda line: line.replace("\n", ""),
        exts=["txt"],
        line_mode=True,
    )
    yaml = FmtProperty(
        writer=lambda f, obj: yaml.dump(obj, f),
        reader=lambda f: yaml.load(f, Loader=yaml.FullLoader),
        exts=["yml", "yaml"],
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


def serialize(
    obj: object,
    fmt: Optional[Fmt] = None,
) -> object:
    """
    Serializes an object into a data structure with only primitive types, list, dict.
    If fmt is provided, its formatting constraints are taken into account. Supported fmts:
    * json, jsonPretty, jsonNoSort, jsonList: dict only have str keys.

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
        return {k: serialize(v, fmt) for k, v in dataclasses.asdict(obj).items()}
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
    else:
        raise TypeError(
            f"Cannot serialize object of type {type(obj)}, please consider writing a serialize() function"
        )

    # TODO: handle numpy arrays, pandas structures, pytorch structures, etc.


class DeserializationError(RuntimeError):
    def __init__(self, data, clz: Optional[Union[Type, str]], reason: str):
        self.data = data
        self.clz = clz
        self.reason = reason

    def __str__(self):
        return f"Cannot deserialize the following data to {self.clz}: {self.reason}\n  {self.data}"


_NON_TYPE = type(None)


def deserialize(
    data,
    clz: Optional[Union[Type, str]] = None,
    error: str = "ignore",
):
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
            raise RuntimeWarning(
                f"The order of items in OrderedDict may not be preserved"
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
            return clz_origin(ret)
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
                t = clz._field_types.get(f)
            else:
                t = None
            if f in data:
                field_values[f] = deserialize(data.get(f), t, error=error)
        return clz(**field_values)

    # DataClass
    if dataclasses.is_dataclass(clz):
        field_values = {}
        for f in dataclasses.fields(clz):
            if f.name in data:
                field_values[f.name] = deserialize(
                    data.get(f.name), f.type, error=error
                )
        return clz(**field_values)

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
        * None: never serialize.
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
