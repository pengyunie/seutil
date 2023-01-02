from pathlib import Path

import pytest
import seutil as su

# sample data that should not require serialization (thus works for all formats)
SAMPLE_DATA = "Hello, world!"
SAMPLE_LIST = [SAMPLE_DATA] * 20


@pytest.mark.parametrize(
    "name", ["a.txt", "a.pkl", "a.pickle", "a.json", "a.yml", "a.yaml"]
)
def test_dump_load_auto_infer(tmp_path: Path, name: str):
    su.io.dump(tmp_path / name, SAMPLE_DATA)
    assert su.io.load(tmp_path / name) == SAMPLE_DATA


@pytest.mark.parametrize(
    "fmt", [fmt for fmt in su.io.fmts.all_fmts if not fmt.line_mode]
)
@pytest.mark.parametrize("compressor", su.io.compressors.all_compressors + [None])
def test_dump_load(tmp_path: Path, fmt: su.io.Formatter, compressor: su.io.Compressor):
    su.io.dump(tmp_path / "a", SAMPLE_DATA, fmt=fmt, compressor=compressor)
    assert su.io.load(tmp_path / "a", fmt=fmt, compressor=compressor) == SAMPLE_DATA


@pytest.mark.parametrize("name", ["a.jsonl"])
def test_dump_load_list_auto_infer(tmp_path: Path, name: str):
    su.io.dump(tmp_path / name, SAMPLE_LIST)
    assert su.io.load(tmp_path / name) == SAMPLE_LIST


@pytest.mark.parametrize("fmt", [fmt for fmt in su.io.fmts.all_fmts if fmt.line_mode])
@pytest.mark.parametrize("compressor", su.io.compressors.all_compressors + [None])
def test_dump_load_list(
    tmp_path: Path, fmt: su.io.Formatter, compressor: su.io.Compressor
):
    su.io.dump(tmp_path / "a", SAMPLE_LIST, fmt=fmt, compressor=compressor)
    assert su.io.load(tmp_path / "a", fmt=fmt, compressor=compressor) == SAMPLE_LIST
