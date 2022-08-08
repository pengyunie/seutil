from pathlib import Path

import pytest
import seutil as su

PREFIX = "testioprefix"
SUFFIX = "testiosuffix"
SEPARATOR = "-X-"


def test_mktmp():
    # Test arguments prefix, suffix, separator
    tmp_file = su.io.mktmp(prefix=PREFIX, suffix=SUFFIX, separator=SEPARATOR)
    assert tmp_file.is_file()
    assert tmp_file.name.startswith(PREFIX + SEPARATOR)
    assert tmp_file.name.endswith(SEPARATOR + SUFFIX)

    # Test using the file
    with open(tmp_file, "wt") as f:
        f.write("aaa")

    with open(tmp_file, "wb") as f:
        f.write(b"aaa")

    su.io.rm(tmp_file)


def test_mktmp_dir():
    # Test arguments prefix, suffix, separator
    tmp_dir = su.io.mktmp_dir(prefix=PREFIX, suffix=SUFFIX, separator=SEPARATOR)
    assert tmp_dir.is_dir()
    assert tmp_dir.name.startswith(PREFIX + SEPARATOR)
    assert tmp_dir.name.endswith(SEPARATOR + SUFFIX)

    # Test using the dir
    with open(tmp_dir / "test.txt", "wt") as f:
        f.write("aaa")

    su.io.rmdir(tmp_dir)


def test_mktmp_argument_dir():
    # Test argument dir of mktmp, mktmp_dir
    tmp_dir_1 = su.io.mktmp_dir()

    tmp_dir_2 = su.io.mktmp_dir(
        prefix=PREFIX, suffix=SUFFIX, separator=SEPARATOR, dir=tmp_dir_1
    )
    assert tmp_dir_2.is_dir()
    assert tmp_dir_2.name.startswith(PREFIX + SEPARATOR)
    assert tmp_dir_2.name.endswith(SEPARATOR + SUFFIX)

    tmp_file = su.io.mktmp(
        prefix=PREFIX, suffix=SUFFIX, separator=SEPARATOR, dir=tmp_dir_1
    )
    assert tmp_file.is_file()
    assert tmp_file.name.startswith(PREFIX + SEPARATOR)
    assert tmp_file.name.endswith(SEPARATOR + SUFFIX)

    su.io.rmdir(tmp_dir_1)


def test_mkdir(tmp_path: Path):
    su.io.mkdir(tmp_path / "test1")


def test_mkdir_fresh(tmp_path: Path):
    # fresh=False should not delete existing content
    temp_dir_2 = tmp_path / "test2"
    su.io.mkdir(temp_dir_2, fresh=False)
    with open(temp_dir_2 / "test.txt", "wt") as f:
        f.write("aaa")
    su.io.mkdir(temp_dir_2, fresh=False)
    assert (temp_dir_2 / "test.txt").is_file()

    # fresh=True should delete existing content
    temp_dir_3 = tmp_path / "test3"
    su.io.mkdir(temp_dir_3, fresh=True)
    with open(temp_dir_3 / "test.txt", "wt") as f:
        f.write("aaa")
    su.io.mkdir(temp_dir_3, fresh=True)
    assert not (temp_dir_3 / "test.txt").is_file()


def test_mkdir_parents(tmp_path: Path):
    # parents=True should create parent files
    su.io.mkdir(tmp_path / "test4" / "ddd", parents=True)
    assert (tmp_path / "test4").is_dir()
    assert (tmp_path / "test4" / "ddd").is_dir()

    # parents=False should raise error
    with pytest.raises(FileNotFoundError):
        su.io.mkdir(tmp_path / "test5" / "ddd", parents=False)


def test_rm(tmp_path):
    # rm file
    f = su.io.mktmp(dir=tmp_path)
    assert f.is_file()
    su.io.rm(f)
    assert not f.is_file()

    # rm dir
    d = su.io.mktmp_dir(dir=tmp_path)
    assert d.is_dir()
    su.io.rm(d)
    assert not d.is_dir()


def test_rm_missing_ok(tmp_path):
    # missing_ok=True should just be fine
    su.io.rm(tmp_path / "abcdefg", missing_ok=True)

    # missing_ok=False should raise error
    with pytest.raises(FileNotFoundError):
        su.io.rm(tmp_path / "abcdefg", missing_ok=False)


def test_rm_force(tmp_path):
    d = su.io.mktmp_dir(dir=tmp_path)
    su.io.mktmp(dir=d)
    assert d.is_dir()

    # force=False should raise error
    with pytest.raises(OSError):
        su.io.rm(d, force=False)
    assert d.is_dir()

    # force=True should be fine
    su.io.rm(d, force=True)
    assert not d.is_dir()


def test_rmdir(tmp_path):
    # rm dir
    d = su.io.mktmp_dir(dir=tmp_path)
    assert d.is_dir()
    su.io.rmdir(d)
    assert not d.is_dir()

    # cannot rm file
    f = su.io.mktmp(dir=tmp_path)
    assert f.is_file()
    with pytest.raises(OSError):
        su.io.rmdir(f)


def test_rmdir_missing_ok(tmp_path):
    # missing_ok=True should just be fine
    su.io.rmdir(tmp_path / "abcdefg", missing_ok=True)

    # missing_ok=False should raise error
    with pytest.raises(FileNotFoundError):
        su.io.rmdir(tmp_path / "abcdefg", missing_ok=False)


def test_rmdir_force(tmp_path):
    d = su.io.mktmp_dir(dir=tmp_path)
    su.io.mktmp(dir=d)
    assert d.is_dir()

    # force=False should raise error
    with pytest.raises(OSError):
        su.io.rmdir(d, force=False)
    assert d.is_dir()

    # force=True should be fine
    su.io.rmdir(d, force=True)
    assert not d.is_dir()


def test_cd(tmp_path):
    d = su.io.mktmp_dir(dir=tmp_path)
    assert Path.cwd() != d
    with su.io.cd(d):
        assert Path.cwd() == d
    assert Path.cwd() != d
