from pathlib import Path
import seutil as su


def test_file_auto_notice(tmp_path: Path):
    f = su.latex.File(tmp_path / "test.tex")
    f.save()
    assert su.io.load(f.path, su.io.Fmt.txt).endswith(
        "test_latex.py test_file_auto_notice\n"
    )
