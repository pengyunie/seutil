from pathlib import Path

import pytest

import seutil as su


def test_file_auto_notice(tmp_path: Path):
    f = su.latex.File(tmp_path / "test.tex")
    f.save()
    assert su.io.load(f.path, su.io.Fmt.txt).endswith(
        "test_latex.py test_file_auto_notice\n"
    )


def test_escape():
    assert su.latex.escape("a") == "a"
    assert su.latex.escape("a & b") == r"a \& b"
    assert su.latex.escape("42%") == r"42\%"
    assert su.latex.escape("$42") == r"\$42"
    assert su.latex.escape("#x") == r"\#x"
    assert su.latex.escape("a_b") == r"a\_b"
    assert su.latex.escape("a{b}") == r"a\{b\}"
    assert su.latex.escape("a~") == r"a\textasciitilde{}"
    assert su.latex.escape("a^") == r"a\textasciicircum{}"
    assert su.latex.escape("a\\") == r"a\textbackslash{}"


def test_latex_text():
    x = su.latex.Text("test")
    assert x.to_latex() == "test"


def test_latex_comment():
    x = su.latex.Comment("test")
    assert x.to_latex() == "%% test\n"


def test_latex_macro_use():
    x = su.latex.MacroUse("test")
    assert x.to_latex() == "\\UseMacro{test}"


def test_latex_macro_def():
    x = su.latex.Macro("test", "value")
    assert x.to_latex() == "\\DefMacro{test}{value}\n"
