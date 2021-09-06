import inspect
import json
import os
import pickle as pkl
import shutil
from enum import Enum
from pathlib import Path
from typing import *
import io

import recordclass
import yaml


def _unify_path(path: Union[str, Path]) -> Path:
    if not isinstance(path, Path):
        path = Path(path)
    return path


def _is_obj_record_class(obj: Any) -> bool:
    return obj is not None \
           and isinstance(obj, recordclass.mutabletuple) or isinstance(obj, recordclass.dataobject)


def _is_clz_record_class(clz: Type) -> bool:
    return clz is not None \
           and inspect.isclass(clz) \
           and (issubclass(clz, recordclass.mutabletuple) or issubclass(clz, recordclass.dataobject))


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
        if missing_ok:
            return
        else:
            raise FileNotFoundError(f"Cannot remove non-exist directory {path}")


def rm(
        path: Union[str, Path],
        missing_ok: bool = True,
        force: bool = True,
        recursive: bool = True,
):
    """
    Removes a file/directory.
    :param path: the name of the file/directory.
    :param missing_ok: (-f) ignores error if the file/directory does not exist.
    :param force: (-f) force remove the file/directory even it's protected.
    :param recursive: (-r) remove the directory even it's empty.
    """
    path = _unify_path(path)
    if path.is_dir():
        if recursive:
            rmdir(path, missing_ok=missing_ok, force=force)
        else:
            path.rmdir()
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

    # If it is a list-like formats (reads/writes one line at a time)
    list_like: bool = False

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
    jsonPretty = json.value._replace(
        writer=lambda f, obj: json.dump(obj, f, sort_keys=True, indent=4),
    )
    # Pretty-print version without sorting keys
    jsonNoSort = json.value._replace(
        writer=lambda f, obj: json.dump(obj, f, indent=4),
    )
    # === jsonl === aka json list
    jsonList = FmtProperty(
        writer=lambda item: json.dumps(item),
        reader=lambda line: json.loads(line),
        exts=["jsonl"],
        list_like=True,
        serialize=True,
    )
    txtList = FmtProperty(
        writer=lambda item: str(item),
        reader=lambda line: line,
        exts=["txt"],
        list_like=True,
    )
    yaml = FmtProperty(
        writer=lambda f, obj: yaml.dump(obj, f),
        reader=lambda f: yaml.load(f, Loader=yaml.FullLoader),
        exts=["yml", "yaml"],
        serialize=True,
    )


def infer_fmt_from_ext(ext: str, default: Optional[Fmt] = None) -> Fmt:
    for fmt in Fmt:
        if fmt.exts is not None and ext in fmt:
            return fmt

    if default is not None:
        return default
    else:
        raise RuntimeError(f"Cannot infer format for extension \"{ext}\"")


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
    :return: the serialized version of the object.
    """
    # Examine the type of object and use the appropriate serialization method
    # Check for simple types first
    if obj is None:
        return None
    elif isinstance(obj, (int, float, str, bool)):
        # Primitive types: keep as-is
        return obj
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
            return serialize(obj.__dict__.items(), fmt)
        else:
            # Newer versions of recordclass
            return serialize(obj.__fields__, fmt)
    else:
        # Custom types: check for "serialize" member function
        if hasattr(obj, "serialize"):
            return getattr(obj, "serialize")()
        else:
            # Last effort: convert to str
            return str(obj)

    # TODO: handle numpy arrays, pandas structures, pytorch structures, etc.
    # TODO: what about NamedTuple?


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

    if append and not fmt.list_like:
        raise RuntimeWarning(f"Appending to a format that's not list-like ({fmt}) may result in invalid file")

    # Serialize (when appropriate)
    if serialization is None:
        serialization = fmt.serialize

    if serialization:
        obj = serialize(obj)

    # Open file
    file_mode = "w" if not append else "a"
    if fmt.binary:
        file_mode += "b"

    with open(path, file_mode) as f:
        # Write content
        if not fmt.list_like:
            fmt.writer(f, obj)
        else:
            for item in obj:
                # Removing all "\n" inside the line
                f.write(fmt.writer(item).replace("\n", " ") + "\n")


# TODO: function deserialize
# TODO: function load
# TODO: create temp file

