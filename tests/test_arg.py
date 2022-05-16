import os

import seutil as su
from jsonargparse import ArgumentParser


def subject_rpath(arg: su.arg.RPath):
    pass


def test_rpath_relative(tmp_path):
    os.chdir(tmp_path)
    parser = ArgumentParser()
    parser.add_function_arguments(subject_rpath)
    cfg = parser.parse_args(["--arg", "bbb"])
    assert cfg.arg == (tmp_path / "bbb").resolve()
    assert not cfg.arg.exists()


def test_rpath_absolute(tmp_path):
    os.chdir(tmp_path)
    parser = ArgumentParser()
    parser.add_function_arguments(subject_rpath)
    cfg = parser.parse_args(["--arg", str(tmp_path)])
    assert cfg.arg == tmp_path.resolve()
    assert cfg.arg.exists()
