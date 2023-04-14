from pathlib import Path

import pytest

import seutil as su

resources_dir = Path(__file__).parent.parent / "resources"
out_dir = Path(__file__).parent / "out"


main_tex_prefix = r"""
\pdfminorversion=7
\documentclass[letter]{article}

%%%----------
%%% Imports

%%% Text Formatting
\usepackage{xspace}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage[normalem]{ulem} % normalem do not replace \emph to underline
\usepackage{amsmath}
\usepackage{enumitem}

%%% Reference, Citation and Link
\usepackage{hyperref}
\hypersetup{linkcolor=black,citecolor=black,anchorcolor=black,filecolor=black,menucolor=black,runcolor=black,urlcolor=black,hidelinks}
%\usepackage{url}
\usepackage{breakurl}
%\usepackage{cite}

%%% Tables
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{makecell}
\usepackage{ragged2e}

%%% Plots
\usepackage{caption}
\usepackage{subcaption}
%\usepackage{subfloat}
%\usepackage{wrapfig}

% Code
\usepackage{listings}

% Tikz Figs
\usepackage{tikz}
%\usepackage{pgf-umlsd} % for flow diagram
\usetikzlibrary{calc}
\usetikzlibrary{shapes.geometric}
\usetikzlibrary{decorations.pathreplacing}
\usetikzlibrary{positioning}
%\usetikzlibrary{shapes}

%%% Miscellaneous
%\usepackage{flushend} % balance the end of double column document
\usepackage{datetime} % for getting current date and time

\usepackage[margin=1in]{geometry}
\usepackage{pdfpages}

\newcommand{\DefMacro}[2]{\expandafter\newcommand\csname rmk-#1\endcsname{#2}}
\newcommand{\UseMacro}[1]{\csname rmk-#1\endcsname}

\title{}
\author{}
"""


class Test_latex_integration:
    """
    Integration test: generate numbers and table tex files, and check
    if they are compilable (requires texlive).
    """

    pd = pytest.importorskip("pandas")

    df_method = pd.read_pickle(resources_dir / "sample-dataset.pkl.gz")

    def test_compile_table(self, request: pytest.FixtureRequest, tmp_path: Path):
        self.gen_numbers(tmp_path)
        self.gen_table(tmp_path)
        su.io.dump(
            tmp_path / "main.tex",
            main_tex_prefix
            + r"""
\DefMacro{TH-num_proj}{\#proj\xspace}
\DefMacro{TH-num_test}{\#test\xspace}
\DefMacro{TH-tok_test}{len(test)\xspace}
\DefMacro{TH-tok_mut}{len(mut)\xspace}
\DefMacro{TH-corpus-all}{all\xspace}
\DefMacro{TH-corpus-train}{train\xspace}
\DefMacro{TH-corpus-val}{val\xspace}
\DefMacro{TH-corpus-test}{test\xspace}
\input{numbers}

\begin{document}
\begin{table}[t]
\begin{center}
\begin{small}
\caption{Example table.\label{tab:example}}
\input{table}
\end{small}
\end{center}
\end{table}
\end{document}
""",
            su.io.Fmt.txt,
        )
        with su.io.cd(tmp_path):
            su.bash.run("latexmk -pdf main.tex", 0)

        # move outputs
        this_out_dir = out_dir / request.node.nodeid
        su.io.mkdir(this_out_dir)
        su.bash.run(f"mv {tmp_path}/* {this_out_dir}/", 0)

    def gen_numbers(self, path: Path):
        f = su.latex.File()
        for subset, subset_fn in [("all", lambda df: df)] + [
            (sn, lambda df, sn=sn: df[df["sn"] == sn])
            for sn in ["train", "val", "test"]
        ]:
            df_subset: self.pd.DataFrame = subset_fn(self.df_method)
            f.append(
                su.latex.Macro(
                    f"corpus-{subset}-num_proj",
                    f"{len(df_subset['proj_name'].unique()):,d}",
                )
            )
            f.append(
                su.latex.Macro(f"corpus-{subset}-num_test", f"{len(df_subset):,d}")
            )
            f.append(
                su.latex.Macro(
                    f"corpus-{subset}-tok_mut",
                    f"{df_subset['num_tok_mut'].mean():,.2f}",
                )
            )
            f.append(
                su.latex.Macro(
                    f"corpus-{subset}-tok_test",
                    f"{df_subset['num_tok_test'].mean():,.2f}",
                )
            )

        f.save(path / "numbers.tex")

    def gen_table(self, path: Path):
        f = su.latex.File()
        f.append(r"\begin{tabular}{l|rrrr}")
        f.append(r"\toprule")
        f.append(r" & \textbf{").append(su.latex.MacroUse("TH-num_proj")).append("}")
        f.append(r" & \textbf{").append(su.latex.MacroUse("TH-num_test")).append("}")
        f.append(r" & \textbf{").append(su.latex.MacroUse("TH-tok_test")).append("}")
        f.append(r" & \textbf{").append(su.latex.MacroUse("TH-tok_mut")).append("}")
        f.append(r" \\")
        f.append(r"\midrule")

        for x in ["all", "train", "val", "test"]:
            f.append(su.latex.MacroUse(f"TH-corpus-{x}"))
            for m in ["num_proj", "num_test", "tok_test", "tok_mut"]:
                f.append(" & ").append(su.latex.MacroUse(f"corpus-{x}-{m}"))
            f.append(r"\\")

        f.append(r"\bottomrule")
        f.append(r"\end{tabular}")
        f.save(path / "table.tex")


class Test_latex_integration_old:
    """
    Integration test: generate numbers and table tex files, and check
    if they are compilable (requires texlive).  Using the old
    deprecated API to maintain backward-compatibility for a while.
    """

    pd = pytest.importorskip("pandas")

    df_method = pd.read_pickle(resources_dir / "sample-dataset.pkl.gz")

    def test_compile_table(self, request: pytest.FixtureRequest, tmp_path: Path):
        self.gen_numbers(tmp_path)
        self.gen_table(tmp_path)
        su.io.dump(
            tmp_path / "main.tex",
            main_tex_prefix
            + r"""
\DefMacro{TH-num_proj}{\#proj\xspace}
\DefMacro{TH-num_test}{\#test\xspace}
\DefMacro{TH-tok_test}{len(test)\xspace}
\DefMacro{TH-tok_mut}{len(mut)\xspace}
\DefMacro{TH-corpus-all}{all\xspace}
\DefMacro{TH-corpus-train}{train\xspace}
\DefMacro{TH-corpus-val}{val\xspace}
\DefMacro{TH-corpus-test}{test\xspace}
\input{numbers}

\begin{document}
\begin{table}[t]
\begin{center}
\begin{small}
\caption{Example table.\label{tab:example}}
\input{table}
\end{small}
\end{center}
\end{table}
\end{document}
""",
            su.io.Fmt.txt,
        )
        with su.io.cd(tmp_path):
            su.bash.run("latexmk -pdf main.tex", 0)

        # move outputs
        this_out_dir = out_dir / request.node.nodeid
        su.io.mkdir(this_out_dir)
        su.bash.run(f"mv {tmp_path}/* {this_out_dir}/", 0)

    def gen_numbers(self, path: Path):
        f = su.latex.File(path / "numbers.tex")
        for subset, subset_fn in [("all", lambda df: df)] + [
            (sn, lambda df, sn=sn: df[df["sn"] == sn])
            for sn in ["train", "val", "test"]
        ]:
            df_subset: self.pd.DataFrame = subset_fn(self.df_method)
            f.append_macro(
                su.latex.Macro(
                    f"corpus-{subset}-num_proj",
                    f"{len(df_subset['proj_name'].unique()):,d}",
                )
            )
            f.append_macro(
                su.latex.Macro(f"corpus-{subset}-num_test", f"{len(df_subset):,d}")
            )
            f.append_macro(
                su.latex.Macro(
                    f"corpus-{subset}-tok_mut",
                    f"{df_subset['num_tok_mut'].mean():,.2f}",
                )
            )
            f.append_macro(
                su.latex.Macro(
                    f"corpus-{subset}-tok_test",
                    f"{df_subset['num_tok_test'].mean():,.2f}",
                )
            )

        f.save()

    def gen_table(self, path: Path):
        f = su.latex.File(path / "table.tex")
        f.append(r"\begin{tabular}{l|rrrr}")
        f.append(r"\toprule")
        f.append(
            " & "
            + r"\textbf{"
            + su.latex.Macro("TH-num_proj").use()
            + "} & "
            + r"\textbf{"
            + su.latex.Macro("TH-num_test").use()
            + "} & "
            + r"\textbf{"
            + su.latex.Macro("TH-tok_test").use()
            + "} & "
            + r"\textbf{"
            + su.latex.Macro("TH-tok_mut").use()
            + r"} \\ "
        )
        f.append(r"\midrule")

        for x in ["all", "train", "val", "test"]:
            f.append(su.latex.Macro(f"TH-corpus-{x}").use())
            for m in ["num_proj", "num_test", "tok_test", "tok_mut"]:
                f.append(" & " + su.latex.Macro(f"corpus-{x}-{m}").use())
            f.append(r"\\")

        f.append(r"\bottomrule")
        f.append(r"\end{tabular}")
        f.save()
