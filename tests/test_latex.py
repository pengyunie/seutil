from pathlib import Path

import pytest

import seutil as su

resources_dir = Path(__file__).parent.parent / "resources"


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


class Test_latex_integration:
    pd = pytest.importorskip("pandas")

    df_method = pd.read_pickle(resources_dir / "sample-dataset.pkl.gz")

    def test_gen_numbers_old(self, tmp_path: Path):
        # deprecated usage example, see `test_gen_numbers` for the updated version
        f = su.latex.File(tmp_path / "numbers.tex")
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

    def test_gen_numbers(self, tmp_path: Path):
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

        f.save(tmp_path / "numbers.tex")

    def test_gen_table_old(self, tmp_path: Path):
        # deprecated usage example, see `test_gen_table` for the updated version
        f = su.latex.File(tmp_path / "table.tex")
        f.append(r"\begin{tabular}{l|rrrr}")
        f.append(r"\toprule")
        f.append(
            " & "
            + r"\textbf{"
            + su.latex.Macro(f"TH-num_proj").use()
            + "} & "
            + r"\textbf{"
            + su.latex.Macro(f"TH-num_test").use()
            + "} & "
            + r"\textbf{"
            + su.latex.Macro(f"TH-tok_test").use()
            + "} & "
            + r"\textbf{"
            + su.latex.Macro(f"TH-tok_mut").use()
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

    def test_gen_table(self, tmp_path: Path):
        f = su.latex.File()
        f.append(r"\begin{tabular}{l|rrrr}")
        f.append(r"\toprule")
        f.append(" & ")
        f.append(r"\textbf{").append(su.latex.MacroUse("TH-num_proj")).append("}")
        f.append(r"\textbf{").append(su.latex.MacroUse("TH-num_test")).append("}")
        f.append(r"\textbf{").append(su.latex.MacroUse("TH-tok_test")).append("}")
        f.append(r"\textbf{").append(su.latex.MacroUse("TH-tok_mut")).append("}")
        f.append(r" \\")
        f.append(r"\midrule")

        for x in ["all", "train", "val", "test"]:
            f.append(su.latex.MacroUse(f"TH-corpus-{x}"))
            for m in ["num_proj", "num_test", "tok_test", "tok_mut"]:
                f.append(" & ").append(su.latex.MacroUse(f"corpus-{x}-{m}"))
            f.append(r"\\")

        f.append(r"\bottomrule")
        f.append(r"\end{tabular}")
        f.save(tmp_path / "table.tex")

    # TODO: add test oracles, to check if the generated tex files can compile (require latex installation), and ideally to check the generated pdf if possible
