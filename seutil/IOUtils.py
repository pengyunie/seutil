import os
import subprocess
import pickle as pkl
import json
import yaml
from collections import defaultdict
from pathlib import Path
from typing import *


class IOUtils:
    """
    Utility functions for I/O.
    """

    # ----------
    # Directory operations

    class cd:
        """
        Change directory. Usage:

        with IOUtils.cd(path):
            <statements>
        # end with

        Using a string path is supported for backward compatibility.
        Using pathlib.Path should be preferred.
        """

        def __init__(self, path: Union[str, Path]):
            if isinstance(path, str):
                path = Path(path)
            # end if
            self.path = path  # Path
            self.old_path = Path.cwd()  # Path
            return

        def __enter__(self):
            os.chdir(self.path)
            return

        def __exit__(self, type, value, tb):
            os.chdir(self.old_path)
            return

    # Deprecated
    # Use pathlib.Path.is_dir() instead
    @classmethod
    def has_dir(cls, dirname) -> bool:
        return os.path.isdir(dirname)

    # Deprecated
    # Use pathlib.Path.mkdir() instead
    @classmethod
    def mk_dir(cls, dirname, mode=0o777,
               is_remove_if_exists: bool = False,
               is_make_parent: bool = True):
        """
        Makes the directory.
        :param dirname: the name of the directory.
        :param mode: mode of the directory.
        :param is_remove_if_exists: if the directory with name already exists, whether to remove.
        :param is_make_parent: if make parent directory if not exists.
        """
        if cls.has_dir(dirname):
            if is_remove_if_exists:
                rm_cmd = "rm {} -rf".format(dirname)
                subprocess.run(["bash", "-c", rm_cmd])
            else:
                return
        # end if
        parent_dir = os.path.dirname(dirname)
        if not cls.has_dir(parent_dir):
            if is_make_parent:
                cls.mk_dir(parent_dir, mode, is_remove_if_exists=False, is_make_parent=True)
            else:
                raise FileNotFoundError("Path not found: {}".format(parent_dir))
        # end if
        os.mkdir(dirname, mode)
        return

    # Deprecated
    # Use shutil.rmtree() instead
    @classmethod
    def rm_dir(cls, dirname,
               is_ok_if_not_exists: bool = True):
        """
        Removes the directory.
        :param dirname: the name of the directory.
        :param is_ok_if_not_exists: if it is OK if the directory does not exist.
        """
        if cls.has_dir(dirname):
            os.rmdir(dirname)
        else:
            if is_ok_if_not_exists:
                return
            else:
                raise FileNotFoundError("Trying to remove non-exist directory {}".format(dirname))
        # end if
        return

    # ----------
    # File operations

    IO_FORMATS = defaultdict(lambda: {
        "mode": "t",
        "dumpf": (lambda obj, f: f.write(obj)),
        "loadf": (lambda f: f.read())
    })
    # pickle (python serialized object)
    IO_FORMATS["pkl"]["mode"] = "b"
    IO_FORMATS["pkl"]["dumpf"] = lambda obj, f: pkl.dump(obj, f)
    IO_FORMATS["pkl"]["loadf"] = lambda f: pkl.load(f)
    # json (human readable version)
    IO_FORMATS["json"]["dumpf"] = lambda obj, f: json.dump(obj, f, indent=4, sort_keys=True)
    IO_FORMATS["json"]["loadf"] = lambda f: yaml.load(f)  # allows some format errors (e.g., trailing commas)
    # json (human readable version)
    IO_FORMATS["json-nosort"]["dumpf"] = lambda obj, f: json.dump(obj, f, indent=4)
    IO_FORMATS["json-nosort"]["loadf"] = lambda f: yaml.load(f)  # allows some format errors (e.g., trailing commas)
    # json_min (minimize size, operation with code only)
    IO_FORMATS["json_min"]["dumpf"] = lambda obj, f: json.dump(obj, f, sort_keys=True)
    IO_FORMATS["json_min"]["loadf"] = lambda f: json.load(f)

    @classmethod
    def dump(cls, file_path: Union[str, Path], obj: object, fmt: str = "json"):
        if isinstance(file_path, str):
            file_path = Path(file_path)
        # end if
        file_path.touch(exist_ok=True)

        conf = cls.IO_FORMATS[fmt]

        with open(file_path, "w" + conf["mode"]) as f:
            conf["dumpf"](obj, f)

        return

    @classmethod
    def load(cls, file_path: Union[str, Path], fmt: str = "json") -> Any:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        # end if

        conf = cls.IO_FORMATS[fmt]

        try:
            with open(file_path, "r" + conf["mode"]) as f:
                obj = conf["loadf"](f)
            # end with
        except FileNotFoundError as e:
            raise FileNotFoundError(str(e) + " at {}".format(Path.cwd()))
        # end try

        return obj

    @classmethod
    def update_json(cls, file_name, data):
        """
        Updates the json data file. The data should be dict like (support update).
        """
        try:
            orig_data = cls.load(file_name)
        except:
            orig_data = dict()
        # end try
        orig_data.update(data)
        cls.dump(file_name, orig_data)
        return orig_data

    @classmethod
    def extend_json(cls, file_name, data):
        """
        Updates the json data file. The data should be list like (support extend).
        """
        try:
            orig_data = cls.load(file_name)
        except:
            orig_data = list()
        # end try
        orig_data.extend(data)
        cls.dump(file_name, orig_data)
        return orig_data

    JSONFY_FUNC_NAME = "jsonfy"
    DEJSONFY_FUNC_NAME = "dejsonfy"
    JSONFY_ATTR_FIELD_NAME = "jsonfy_attr"

    @classmethod
    def jsonfy(cls, obj):
        """
        Turns an object to a json-compatible data structure.
        A json-compatible data can only have list, dict (with str keys), str, int and float.
        Any object of other classes will be casted through (try each option in order, if applicable):
        1. JSONFY function, which takes no argument and returns a json-compatible data;
           should have the name {@link IOUtils#JSONFY_FUNC_NAME};
        2. JSONFY_ATTR field, which is a dict of attribute name-type pairs, that will be extracted from the object to a dict;
           should have the name {@link IOUtils#JSONFY_ATTR_FIELD_NAME};
        3. cast to a string.
        """
        if obj is None:
            return None
        elif isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, str):
            return obj
        elif isinstance(obj, list) or isinstance(obj, set):  # TODO: support set also in dejsonfy
            return [cls.jsonfy(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: cls.jsonfy(v) for k, v in obj.items()}
        elif hasattr(obj, cls.JSONFY_FUNC_NAME):
            return getattr(obj, cls.JSONFY_FUNC_NAME)()
        elif hasattr(obj, cls.JSONFY_ATTR_FIELD_NAME):
            return {attr: cls.jsonfy(getattr(obj, attr)) for attr in getattr(obj, cls.JSONFY_ATTR_FIELD_NAME).keys()}
        else:
            return repr(obj)

    @classmethod
    def dejsonfy(cls, data, clz=None):
        """
        Turns a json-compatible data structure to an object of class {@code clz}.
        If {@code clz} is not assigned, the data will be casted to dict or list if possible.
        Otherwise the data will be casted to the object through (try each option in order, if applicable):
        1. DEJSONFY function, which takes the data as argument and returns a object;
           should have the name {@link IOUtils#DEJSONFY_FUNC_NAME};
        2. JSONFY_ATTR field, which is a dict of attribute name-type pairs, that will be extracted from the object to a dict;
           should have the name {@link IOUtils#JSONFY_ATTR_FIELD_NAME};
        """
        if isinstance(clz, str):
            clz = globals()[clz]
        # end if

        if data is None:
            return None
        elif isinstance(data, list):
            return [cls.dejsonfy(item, clz) for item in data]
        elif clz is not None and hasattr(clz, cls.DEJSONFY_FUNC_NAME):
            return clz.dejsonfy(data)
        elif clz is not None and hasattr(clz, cls.JSONFY_ATTR_FIELD_NAME):
            obj = clz()
            for attr, attr_clz in getattr(clz, cls.JSONFY_ATTR_FIELD_NAME).items():
                if attr in data:
                    setattr(obj, attr, cls.dejsonfy(data[attr], attr_clz))
            # end for, if
            return obj
        elif isinstance(data, dict):
            return {k: cls.dejsonfy(v, clz) for k, v in data.items()}
        else:
            return data
