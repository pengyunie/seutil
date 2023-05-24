"""
Utilities for generating/manipulating latex files.

Some parts inspired by https://github.com/JelteF/PyLaTeX, but this module means to be more lightweight.
"""

import abc
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import io, log

logger = log.get_logger("latex")

__all__ = ["LatexItem", "File"]


def escape(s: str) -> str:
    """
    Escapes a string for latex.
    """
    escaped = ""
    for c in s:
        if c in "&%$#_{}":
            escaped += "\\" + c
        elif c == "~":
            escaped += r"\textasciitilde{}"
        elif c == "^":
            escaped += r"\textasciicircum{}"
        elif c == "\\":
            escaped += r"\textbackslash{}"
        else:
            escaped += c
    return escaped


class LatexItem:
    @abc.abstractmethod
    def to_latex(self) -> str:
        raise NotImplementedError()


class Text(LatexItem):
    def __init__(self, s: str):
        self.s = s

    def to_latex(self) -> str:
        return self.s


class Comment(LatexItem):
    def __init__(self, s: str):
        self.s = s

    def to_latex(self) -> str:
        return f"%% {self.s}\n"


class MacroUse(LatexItem):
    USEMACRO_COMMAND = "UseMacro"

    def __init__(self, key: str):
        self.key = key

    def to_latex(self) -> str:
        return "\\" + self.USEMACRO_COMMAND + "{" + self.key + "}"


class Macro(LatexItem):
    DEFMACRO_COMMAND = "DefMacro"
    RE_DEF_MACRO = re.compile(r"\\DefMacro{(?P<key>[^}]+)}{(?P<value>[^}]*)}")

    def __init__(self, key: str, value: Optional[Any] = None):
        self.key = key
        self.value = value

    def use(self) -> str:
        # deprecated: use `MacroUse` instead
        return "\\" + MacroUse.USEMACRO_COMMAND + "{" + self.key + "}"

    def to_latex(self) -> str:
        if self.value is None:
            raise ValueError(f"Macro {self.key} has no value")
        s = "\\" + self.DEFMACRO_COMMAND + "{" + self.key + "}{" + str(self.value) + "}\n"
        return s

    @classmethod
    def load_from_file(cls, file: Path) -> Dict[str, "Macro"]:
        """
        Loads the macros from a latex file.
        Will convert the value of the macros to int or float, if possible.
        TODO: does not work if the macro spans multiple lines.

        :param file: the latex file.
        :return: the indexed dictionary of {macro.key, macro}.
        """
        macros_indexed: Dict[str, Macro] = dict()

        lines: List[str] = io.load(file, io.fmts.txtList)
        for line in lines:
            match = cls.RE_DEF_MACRO.fullmatch(line.strip())
            if match is not None:
                key = match.group("key")
                value = match.group("value")

                # Try to convert to int, then (if failing) float.
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

                macros_indexed[key] = Macro(key, value)

        return macros_indexed


class File(LatexItem):
    class NewlineMode(Enum):
        auto = "auto"
        always = "always"
        never = "never"

    def __init__(
        self,
        path: Optional[Path] = None,
        is_append: Optional[bool] = None,
        auto_notice: bool = True,
        newline_mode: Union[NewlineMode, str] = NewlineMode.auto,
    ):
        """
        Creates a latex file which holds a list of items.
        :param path: the path to use when saving the file; this parameter can also be provided to the save() method.
        :param is_append: if the file already exists, whether to append to it, otherwise overwrite it; this parameter can also be provided to the save() method.
        :param auto_notice: whether to automatically add a notice comment in the generated file which contains the name of the script file and function.
        :param newline_mode: mode for inserting newlines between items:
            - auto: (default) insert newlines if the previous item doesn't end with newline.
            - always: always insert newlines.
            - never: never insert newlines.
        TODO: eventually make sure all items that are sensitive to newlines insert newlines for themselves, and change the default to never.
        """
        self.path: Optional[Path] = path
        self.is_append: Optional[bool] = is_append
        self.auto_notice: bool = auto_notice
        self.newline_mode: File.NewlineMode = File.NewlineMode(newline_mode)
        self.items: List[LatexItem] = []

    def to_latex(self) -> str:
        out = ""
        for item in self.items:
            if self.newline_mode == File.NewlineMode.always:
                out += "\n"
            elif self.newline_mode == File.NewlineMode.auto and not out.endswith("\n"):
                out += "\n"
            out += item.to_latex()
        return out

    def save(self, path: Optional[Path] = None, is_append: Optional[bool] = None):
        """
        Saves the file to the given path.
        :param path: the path to use when saving the file; this parameter override the path provided in the constructor.
        :param is_append: if the file already exists, whether to append to it, otherwise overwrite it.
        """
        if path is None:
            if self.path is None:
                raise ValueError("Path for saving the file not specified")
            else:
                path = self.path

        if is_append is None:
            if self.is_append is None:
                is_append = False
            else:
                is_append = self.is_append

        # the main content of the file
        s = self.to_latex()

        # figure out whether we need to append to a file
        appending = is_append and path.exists()
        if appending:
            s = io.load(path, io.fmts.txt) + s

        # add the auto notice (only if it is a new file)
        if self.auto_notice and not appending:
            src = sys._getframe(1).f_code
            s = f"%% Automatically generated by: {Path(src.co_filename).name} {src.co_name}\n" + s

        # save
        io.dump(path, s, io.fmts.txt)

    def append(self, item: Union[str, LatexItem]) -> "File":
        if isinstance(item, str):
            item = Text(item)
        self.items.append(item)
        return self

    def append_comment(self, s: str) -> "File":
        return self.append(Comment(s))

    def append_macro(self, macro: Macro) -> "File":
        # deprecated: use `append` instead
        return self.append(macro)
