from pathlib import Path
import re
from typing import *
from .. import LoggingUtils, IOUtils


class Macro:

    logger = LoggingUtils.get_logger("latex.Macro")

    T = TypeVar("T")
    def __init__(self,
                 key: str,
                 value: Optional[T] = None,
                 value_func: Optional[Callable[[Dict[str, "Macro"]], T]] = None,
                 tostring_func: Optional[Callable[[T], str]] = None):
        """
        Defines a latex macro, using "\DefMacro{key}{value}".
        :param key: the key of the macro.
        :param value: the value of the macro, can be None.
        :param value_func: the (lazily evaluated) function to get the value of the macro, can be None. The function will receive one argument of a dictionary of {macro.key, macro} of macros defined in the same file, and should return the evaluated value.
        :param tostring_func: the function to format the value to string, can be None. If set to None, __str__() will be used.
        """
        self.key: str = key
        self.value: Optional[Macro.T] = value
        self.value_func: Optional[Callable[[Dict[str, Macro]], Macro.T]] = value_func
        self.tostring_func: Optional[Callable[[Macro.T], str]] = tostring_func
        return

    def eval_content(self, macros_indexed: Dict[str, "Macro"]) -> str:
        """
        Evaluates the latex macro, and formats to a string that defines the macro (i.e., \DefMacro{key}{value}).
        If both value and value_func are defined, will use the value_func to update the value.

        :param macros_indexed: the indexed dictionary of {macro.key, macro}.
        :requires: not (self.value is None and self.value_func is None)
        :return: the string representation of the macro.
        """
        if self.value is None and self.value_func is None:
            raise ValueError("Cannot evaluate a macro without any value definition")
        # end if

        if self.value_func is not None:
            self.value = self.value_func(macros_indexed)
        # end if
        self.logger.info(f"Macro {self.key} evaluates to {self.value}")

        tostring_func = self.tostring_func if self.tostring_func is not None else str
        return f"\\DefMacro{{{self.key}}}{{{tostring_func(self.value)}}}"

    # Deprecated
    @classmethod
    def define(cls, key: str, value_fmt: Union[str, Any], *values, **values_items) -> "Macro":
        if len(values) != 0 or len(values_items) != 0:
            return Macro(key, value=value_fmt.format(*values, **values_items))
        else:
            return Macro(key, value=value_fmt)
        # end if

    def use(self) -> str:
        latex_line = f"\\UseMacro{{{self.key}}}"
        return latex_line

    RE_DEF_MACRO = re.compile(r"\\DefMacro{(?P<key>[^}]+)}{(?P<value>[^}]*)}")

    @classmethod
    def load_from_file(cls, file: Path) -> Dict[str, "Macro"]:
        """
        Loads the macros from a latex file.
        Will convert the value of the macros to int or float, if possible.

        :param file: the latex file.
        :return: the indexed dictionary of {macro.key, macro}.
        """
        macros_indexed: Dict[str, Macro] = dict()

        lines: List[str] = IOUtils.load(file, "txt").split("\n")
        for line in lines:
            match = cls.RE_DEF_MACRO.fullmatch(line.strip())
            if match is not None:
                key = match.group("key")
                value = match.group("value")

                # Try to convert to int, then (if failing) float.
                try:
                    value = int(value)
                except:
                    try:
                        value = float(value)
                    except:
                        pass
                # end try, try

                macros_indexed[key] = Macro(key, value)
            # end if
        # end for

        return macros_indexed
