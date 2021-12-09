import inspect
import sys
from typing import *

from recordclass import RecordClass

from seutil import LoggingUtils

__all__ = [
    "Arg", "Args", "parse", "get_targets", "dispatch",
]


logger = LoggingUtils.get_logger("seutil.args")


class Arg(NamedTuple):
    value: Optional[Union[str, List[str]]] = None

    def as_bool(self) -> bool:
        if self.value is None:
            return True
        elif isinstance(self.value, str):
            if self.value in ["t", "T", "true", "True"]:
                return True
            elif self.value in ["f", "F", "false", "False"]:
                return False
            raise TypeError(f"Cannot convert value \"{self.value}\" to bool.")
        else:  # list
            raise TypeError(f"Cannot convert multiple ({(len(self.value))}) values to bool.")

    @property
    def bool_(self) -> bool:
        return self.as_bool()

    def as_str(self) -> str:
        if self.value is None:
            raise TypeError(f"Cannot convert empty value to str.")
        if isinstance(self.value, list):
            raise TypeError(f"Cannot convert multiple ({len(self.value)}) values to str.")
        return self.value

    @property
    def str_(self) -> str:
        return self.as_str()

    def as_int(self) -> int:
        if self.value is None:
            raise TypeError(f"Cannot convert empty value to int.")
        if isinstance(self.value, list):
            raise TypeError(f"Cannot convert multiple ({len(self.value)}) values to int.")
        try:
            return int(self.value)
        except:
            raise TypeError(f"Cannot convert value \"{self.value}\" to int.")

    @property
    def int_(self):
        return self.as_int()

    def as_float(self) -> float:
        if self.value is None:
            raise TypeError(f"Cannot convert empty value to float.")
        if isinstance(self.value, list):
            raise TypeError(f"Cannot convert multiple ({len(self.value)}) values to float.")
        try:
            return float(self.value)
        except:
            raise TypeError(f"Cannot convert value \"{self.value}\" to float.")

    @property
    def float_(self):
        return self.as_float()

    def as_auto(self) -> Union[int, float, str, bool, list]:
        if self.value is None:
            return None
        elif isinstance(self.value, list):
            return [Arg(v).as_auto() for v in self.value]
        else:  # str
            if self.value in ["true", "True"]:
                return True
            if self.value in ["false", "False"]:
                return False

            try:
                intval = int(self.value)
            except:
                pass
            else:
                return intval

            try:
                floatval = float(self.value)
            except:
                pass
            else:
                return floatval

            return self.value

    @property
    def auto_(self):
        return self.as_auto()

    def as_dtype(self, dtype: type = None) -> Optional[Union[int, float, str, bool]]:
        if dtype is None:
            return self.as_auto()
        elif dtype == str:
            return self.as_str()
        elif dtype == int:
            return self.as_int()
        elif dtype == float:
            return self.as_float()
        elif dtype == bool:
            return self.as_bool()
        else:
            raise TypeError(f"Unsupported dtype {dtype}.")

    def as_list(self, dtype: type = None) -> list:
        if self.value is None:
            return []
        elif not isinstance(self.value, list):
            return [self.as_dtype(dtype)]
        else:
            return [Arg(v).as_dtype(dtype) for v in self.value]

    @property
    def list_(self):
        return self.as_list()

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()


class Args(NamedTuple):
    free: List[Arg] = None
    named: Dict[str, Arg] = None

    def __getitem__(self, key: Union[str, int]) -> Arg:
        if isinstance(key, int):
            return self.free[key]
        else:
            return self.named[key]

    def get(self, key: Union[str, int], default: Union[str, int, float, list, None] = None) -> Arg:
        ret = None
        if isinstance(key, int):
            if key <= len(self.free):
                ret = self.free[key]
        else:
            if key in self.named:
                ret = self.named[key]

        if ret is None:
            return Arg(default)
        else:
            return ret

    def __len__(self):
        return len(self.free) + len(self.named)

    def __str__(self):
        s = f"Free args: ({len(self.free)})\n"
        s += f"  {self.free}\n"
        s += f"Named args: ({len(self.named)})\n"
        for k, v in self.named.items():
            s += f"  {k}: {v}\n"
        return s

    def __repr__(self):
        return self.__str__()

    def fill_signature(self, sig: inspect.Signature) -> inspect.BoundArguments:
        # TODO: fill in **options arg
        # TODO: log more about untyped values, mismatch types, etc.
        # TODO: support automatically convert str to Path.
        params_type_args = []
        kwargs = {}
        missing_params = []
        var_positional_name = None
        for name, param in sig.parameters.items():
            if param.annotation == Args:
                params_type_args.append(name)
            elif name in self.named:
                # Matching arg name and param name: try to fill in this param
                dtype = None
                as_list = False
                if param.annotation in [int, float, bool]:
                    dtype = param.annotation
                elif param.annotation == list or get_origin(param.annotation) == list:
                    as_list = True
                    if get_args(param.annotation) is not None and len(get_args(param.annotation)) > 0:
                        if get_args(param.annotation)[0] in [int, float, bool]:
                            dtype = get_args(param.annotation)[0]

                if not as_list:
                    kwargs[name] = self.named[name].as_dtype(dtype)
                else:
                    kwargs[name] = self.named[name].as_list(dtype)
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                var_positional_name = name
            elif param.default == inspect.Parameter.empty:
                missing_params.append(name)

        if len(params_type_args) == 1:
            # If exactly one parameter has the type of Args, bound this object to that parameter
            logger.info(f"Binding the entire args to {params_type_args[0]}")
            ret = sig.bind_partial(**{params_type_args[0]: self})
        else:
            # Otherwise, try to assign fields from arguments to the parameters with appropriate types
            # Warn about missing params
            if len(missing_params) > 0:
                logger.warning(f"The following parameters may be missing: {missing_params}")

            # Debug about unused args
            unused_args = [k for k in self.named if k not in kwargs]
            if len(unused_args) > 0:
                logger.info(f"The following named arguments are not used: {unused_args}")

            # If there is a *param parameter not already filled, put the free arguments in
            if var_positional_name is not None:
                kwargs[var_positional_name] = [arg.auto_ for arg in self.free]
            else:
                logger.info(f"The following free arguments are not used: {self.free}")

            ret = sig.bind_partial(**kwargs)
        ret.apply_defaults()
        return ret

    def fill_dict(self, obj: dict, dtype: Union[type, str, Dict[str, type]] = "infer") -> dict:
        ...

    def fill_named_tuple(self, obj: NamedTuple, dtype: Union[type, str, Dict[str, type]] = "infer") -> NamedTuple:
        ...

    def fill_record_class(self, obj: RecordClass, dtype: Union[type, str, Dict[str, type]] = "infer") -> RecordClass:
        ...


def parse(
        argv: List[str],
        allow_sep_ws: bool = True,
        allow_sep_equal: bool = True,
        free_args_indicator: bool = True,
        gather_nargs: bool = True,
        multi_args: str = "gather",
) -> Args:
    """
    Parses the command line arguments into an Args object with simple rules.

    Examples of supported command line args:
    `-a 1 -b 2 --color red` -> {"a": 1, "b": 2, "color": "red"}  // allow_sep_ws=True
    `-a=1 -b=2 --color=red` -> {"a": 1, "b": 2, "color": "red"}  // allow_sep_equal=True
    `--nargs 1 2 3 4 -other=5` -> {"nargs": [1, 2, 3, 4], "other": 5}  // gather_nargs=True
                               -> [2, 3, 4], {"nargs": 1, "other": 5}  // gather_args=False
    `-opt=1 -opt=2 -opt=3` -> {"opt": [1, 2, 3]}  // multi_args="gather"
                           -> {"opt": 1}  // multi_args="first"
                           -> {"opt": 3}  // multi_args="last"
    `action -a 1`  -> ["action"], {"a": 1}

    :param argv: the list of command line arguments to parse (usually, sys.argv[1:]).
    :param allow_sep_ws: whether to use whitespace as separator between arg name and value.
    :param allow_sep_equal: whether to use "=" as separator between arg name and value.
    :param free_args_indicator: whether to use "--" to indicate all remaining args as free args.
    :param gather_nargs: whether to gather multiple arg values after an arg name; only applied if allow_sep_ws=True.
    :param multi_args: what to do if an arg name is supplied multiple times:
        * gather (default):  gather them as a list.
        * first:  only keep the first one.
        * last:  only keep the last one.
    :return: an Args object, which stores all free and named args, and supports converting
        them into bool/int/float/list automatically or manually.
    """
    if not allow_sep_ws and not allow_sep_equal:
        raise RuntimeError("Cannot disable both ws and equal separators.")
    if not allow_sep_ws:
        gather_nargs = False
    assert multi_args in ["gather", "first", "last"]

    free = []
    named = {}

    free_args_indicated = False

    i = 0
    while i < len(argv):
        arg = argv[i]
        if free_args_indicator and arg == "--":
            free_args_indicated = True
        elif free_args_indicated:
            free.append(Arg(arg))
        elif arg.startswith("-"):
            values = []
            name = arg
            if allow_sep_equal:
                parts = arg.split("=", 1)
                name = parts[0]
                if len(parts) > 1:
                    values.append(parts[1])

            name = name.lstrip("-")

            if allow_sep_ws:
                while i + 1 < len(argv):
                    if argv[i+1].startswith("-"):
                        break
                    if not gather_nargs and len(values) >= 1:
                        break
                    values.append(argv[i+1])
                    i += 1

            if len(values) == 0:
                value = None
            elif len(values) == 1:
                value = values[0]
            else:
                value = values

            if name not in named:
                named[name] = Arg(value)
            else:
                if multi_args == "first":
                    pass
                elif multi_args == "last":
                    named[name] = Arg(value)
                else:  # "gather"
                    new_value = []
                    if isinstance(named[name].value, list):
                        new_value += named[name].value
                    elif named[name].value is not None:
                        new_value.append(named[name].value)
                    if isinstance(value, list):
                        new_value += value
                    elif value is not None:
                        new_value.append(value)
                    named[name] = Arg(new_value)
        else:
            free.append(Arg(arg))

        i += 1

    return Args(free=free, named=named)


def get_targets(module_name: str) -> Dict[str, Callable]:
    """Gets all the function targets in a module."""
    targets = {}
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if inspect.isfunction(obj):
            targets[name] = obj
    return targets


def dispatch(
        argv: List[str],
        targets: Dict[str, Callable],
        default_target: str = "main",
):
    """
    Dispatches the arguments to one of the targets.  The target name should be specified as the first free argument,
    or the default target is used.
    :param argv:
    :param targets:
    :param default_target:
    :return:
    """
    logger = LoggingUtils.get_logger("args.main")
    logger.info("Starting")

    args = parse(argv)
    if len(args.free) > 0:
        target = args.free[0]
        args = args._replace(free=args.free[1:])
    else:
        target = default_target

    if target not in targets:
        raise RuntimeError(f"Cannot find target {target} in the available set of targets: {targets.keys()}")
    else:
        f = targets[target]
        sig = inspect.Signature.from_callable(f)
        bounded_args = args.fill_signature(sig)
        ret = f(*bounded_args.args, **bounded_args.kwargs)
        logger.info("Terminating")
        return ret
