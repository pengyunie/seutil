from pathlib import Path

import seutil as su


def test_file_auto_notice(tmp_path: Path):
    f = su.latex.File(tmp_path / "test.tex")
    f.save()
    assert su.io.load(f.path, su.io.fmts.txt).endswith("test_latex.py test_file_auto_notice\n")


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


def test_latex_macro_def_int():
    x = su.latex.Macro("test", 42)
    assert x.to_latex() == "\\DefMacro{test}{42}\n"


def test_latex_macro_def_float():
    x = su.latex.Macro("test", 42.0)
    assert x.to_latex() == "\\DefMacro{test}{42.0}\n"


def test_latex_macro_load_from_file(tmp_path: Path):
    su.io.dump(
        tmp_path / "macros.tex",
        r"""
\DefMacro{test1}{1}
\DefMacro{test2}{2.0}
\DefMacro{test3}{4.2}
\DefMacro{test4}{some text\xspace}
""",
        su.io.fmts.txt,
    )
    macros = su.latex.Macro.load_from_file(tmp_path / "macros.tex")
    assert macros["test1"].value == 1
    assert macros["test2"].value == 2.0
    assert macros["test3"].value == 4.2
    assert macros["test4"].value == r"some text\xspace"
