import logging
import os
from pathlib import Path

import pytest
import seutil as su

resources_dir = Path(__file__).parent.parent / "resources"


# we use the https://github.com/git-game/git-game as the test subject for the project module; I checkpointed the state of the repository on 2022-05-11 --- forked to my github account, and also downloaded+compressed as a tgz.


@pytest.fixture
def local_gitgame_repo(tmp_path: Path):
    """The git-game repo comes with this project as a test subject."""
    os.chdir(tmp_path)
    git_game_tgz = resources_dir / "git-game.git.tgz"
    su.bash.run(f"tar -xzf {git_game_tgz}", 0)

    return su.project.Project(
        full_name="pengyunie_git-game",
        url=f"file://{tmp_path.absolute()}/git-game.git",
        data={"metadata1": "aaa", "metadata2": "bbb"},
    )


@pytest.fixture
def remote_gitgame_repo():
    """The git-game repo on github."""
    return su.project.Project(
        full_name="pengyunie_git-game",
        url=f"https://github.com/pengyunie/git-game.git",
        data={"metadata1": "aaa", "metadata2": "bbb"},
    )


REMOTE_GITGAME_REPO_JSON = {
    "full_name": "pengyunie_git-game",
    "url": "https://github.com/pengyunie/git-game.git",
    "metadata1": "aaa",
    "metadata2": "bbb",
}


def test_deserialize(remote_gitgame_repo: su.project.Project):
    assert (
        su.io.deserialize(REMOTE_GITGAME_REPO_JSON, su.project.Project)
        == remote_gitgame_repo
    )


def test_serialize(remote_gitgame_repo: su.project.Project):
    assert su.io.serialize(remote_gitgame_repo) == REMOTE_GITGAME_REPO_JSON


def test_clone_local(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (tmp_path / "pengyunie_git-game" / ".git").exists()
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"


def test_clone_local_name(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path, name="aaa")
    assert (tmp_path / "aaa").exists()
    assert (tmp_path / "aaa" / ".git").exists()
    assert local_gitgame_repo.dir == tmp_path / "aaa"


def test_clone_local_exists_ignore(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()

    local_gitgame_repo.clone(tmp_path, exists="ignore")
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (tmp_path / "pengyunie_git-game" / ".git").exists()
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"


def test_clone_local_exists_remove(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    # touch a random file in the cloned directory, to test if it is later removed
    su.io.dump(local_gitgame_repo.dir / "random.txt", "abc", su.io.Fmt.txt)
    assert (local_gitgame_repo.dir / "random.txt").exists()

    local_gitgame_repo.clone(tmp_path, exists="remove")
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (tmp_path / "pengyunie_git-game" / ".git").exists()
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"
    assert not (local_gitgame_repo.dir / "random.txt").exists()


def test_clone_local_exists_pull(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )
    # undo the last commit, to test if it is later pulled back
    with su.io.cd(local_gitgame_repo.dir):
        su.bash.run("git reset --hard HEAD~1", 0)
    assert (
        local_gitgame_repo.get_cur_revision()
        == "7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30"
    )

    local_gitgame_repo.clone(tmp_path, exists="pull")
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (tmp_path / "pengyunie_git-game" / ".git").exists()
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"
    with su.io.cd(local_gitgame_repo.dir):
        su.bash.run("git checkout origin/master", 0)
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )


def test_clone_local_exists_error(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()

    with pytest.raises(RuntimeError):
        local_gitgame_repo.clone(tmp_path, exists="error")


@pytest.mark.slow  # TODO: mark this item as something like "need internet" instead
def test_clone_remote(remote_gitgame_repo: su.project.Project, tmp_path: Path):
    remote_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (tmp_path / "pengyunie_git-game" / ".git").exists()
    assert remote_gitgame_repo.dir == tmp_path / "pengyunie_git-game"


# for the remaining tests about the operations after cloning, it does not matter if the project is from local or online


def test_set_cloned_dir(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (tmp_path / "pengyunie_git-game" / ".git").exists()
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"

    su.bash.run(
        f"mv {tmp_path / 'pengyunie_git-game'} {tmp_path / 'pengyunie_git-game2'}", 0
    )
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"

    local_gitgame_repo.set_cloned_dir(tmp_path / "pengyunie_git-game2")
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game2"


def test_remove(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert local_gitgame_repo.dir == tmp_path / "pengyunie_git-game"

    local_gitgame_repo.remove()
    assert not (tmp_path / "pengyunie_git-game").exists()
    with pytest.raises(RuntimeError):
        local_gitgame_repo.dir


def test_fetch(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )
    # undo the last commit, to test if it is later pulled back
    with su.io.cd(local_gitgame_repo.dir):
        su.bash.run("git reset --hard HEAD~1", 0)
    assert (
        local_gitgame_repo.get_cur_revision()
        == "7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30"
    )

    local_gitgame_repo.fetch()
    with su.io.cd(local_gitgame_repo.dir):
        su.bash.run("git checkout origin/master", 0)
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )


def test_checkout(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )
    local_gitgame_repo.checkout("7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30")
    assert (
        local_gitgame_repo.get_cur_revision()
        == "7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30"
    )


def test_checkout_forced(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )
    # modify the README so that normal checkout should fail
    su.io.dump(local_gitgame_repo.dir / "README.md", "modified", su.io.Fmt.txt)
    with pytest.raises(su.bash.BashError):
        local_gitgame_repo.checkout("7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30")

    # a forced checkout should do it
    local_gitgame_repo.checkout("7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30", forced=True)
    assert (
        local_gitgame_repo.get_cur_revision()
        == "7c8c3ccc2f4bb118a657f1f7a7ab4e163d1b7a30"
    )


def test_get_cur_revision(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()
    assert (
        local_gitgame_repo.get_cur_revision()
        == "d851edda3009332dd5d3f8f949a102f279dad809"
    )


def test_get_revisions_lattice(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)
    assert (tmp_path / "pengyunie_git-game").exists()

    lattice = local_gitgame_repo.get_revisions_lattice()
    assert lattice.ncount() == 6
    assert lattice.ecount() == 5


def test_from_github_url():
    for url in [
        "https://github.com/pengyunie/seutil",
        "https://github.com/pengyunie/seutil.git",
        "git@github.com:pengyunie/seutil.git",
    ]:
        proj = su.project.Project.from_github_url(url)
        assert proj.url == url
        assert proj.full_name == "pengyunie_seutil"


def test_from_github_url_invalid():
    with pytest.raises(ValueError):
        su.project.Project.from_github_url("http://github.com/pengyunie/seutil")


def test_for_each_revision(local_gitgame_repo: su.project.Project, tmp_path: Path):
    local_gitgame_repo.clone(tmp_path)

    lattice = local_gitgame_repo.get_revisions_lattice()
    revisions = [n["revision"] for n in lattice.nodes()]

    def action(p: su.project.Project, r: str):
        return (p.get_cur_revision(), su.bash.run("pwd").stdout.strip())

    ret = local_gitgame_repo.for_each_revision(action, revisions)
    assert [x[0] for x in ret] == revisions
    assert [Path(x[1]) for x in ret] == [local_gitgame_repo.dir] * len(revisions)


def test_for_each_revision_no_auto_checkout(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)

    lattice = local_gitgame_repo.get_revisions_lattice()
    revisions = [n["revision"] for n in lattice.nodes()]
    local_gitgame_repo.checkout(revisions[0])

    def action(p: su.project.Project, r: str):
        return (p.get_cur_revision(), su.bash.run("pwd").stdout.strip())

    ret = local_gitgame_repo.for_each_revision(action, revisions, auto_checkout=False)
    assert [x[0] for x in ret] == [revisions[0]] * len(revisions)
    assert [Path(x[1]) for x in ret] == [local_gitgame_repo.dir] * len(revisions)


def test_for_each_revision_errors_ignore(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)

    lattice = local_gitgame_repo.get_revisions_lattice()
    revisions = [n["revision"] for n in lattice.nodes()]

    def action(p: su.project.Project, r: str):
        nonlocal revisions
        if r == revisions[0]:
            raise Exception("error")
        return (p.get_cur_revision(), su.bash.run("pwd").stdout.strip())

    ret = local_gitgame_repo.for_each_revision(action, revisions, errors="ignore")
    assert [x[0] for x in ret] == revisions[1:]
    assert [Path(x[1]) for x in ret] == [local_gitgame_repo.dir] * (len(revisions) - 1)


def test_for_each_revision_errors_warning(
    local_gitgame_repo: su.project.Project,
    tmp_path: Path,
    recwarn: pytest.WarningsRecorder,
):
    local_gitgame_repo.clone(tmp_path)

    lattice = local_gitgame_repo.get_revisions_lattice()
    revisions = [n["revision"] for n in lattice.nodes()]

    def action(p: su.project.Project, r: str):
        nonlocal revisions
        if r == revisions[0]:
            raise Exception("error")
        return (p.get_cur_revision(), su.bash.run("pwd").stdout.strip())

    recwarn.clear()
    ret = local_gitgame_repo.for_each_revision(action, revisions, errors="warning")
    assert len(recwarn.list) == 1
    assert [x[0] for x in ret] == revisions[1:]
    assert [Path(x[1]) for x in ret] == [local_gitgame_repo.dir] * (len(revisions) - 1)


def test_for_each_revision_errors_collate(
    local_gitgame_repo: su.project.Project,
    tmp_path: Path,
    recwarn: pytest.WarningsRecorder,
):
    local_gitgame_repo.clone(tmp_path)

    lattice = local_gitgame_repo.get_revisions_lattice()
    revisions = [n["revision"] for n in lattice.nodes()]
    assert len(revisions) >= 2

    def action(p: su.project.Project, r: str):
        nonlocal revisions
        if r == revisions[0] or r == revisions[-1]:
            raise Exception("error")
        return (p.get_cur_revision(), su.bash.run("pwd").stdout.strip())

    recwarn.clear()
    with pytest.raises(su.project.CollatedErrors) as exc_info:
        local_gitgame_repo.for_each_revision(action, revisions, errors="collate")

    assert exc_info.value.contexts == [revisions[0], revisions[-1]]
    assert len(recwarn.list) == 2


def test_for_each_revision_errors_error(
    local_gitgame_repo: su.project.Project, tmp_path: Path
):
    local_gitgame_repo.clone(tmp_path)

    lattice = local_gitgame_repo.get_revisions_lattice()
    revisions = [n["revision"] for n in lattice.nodes()]
    assert len(revisions) >= 2

    def action(p: su.project.Project, r: str):
        nonlocal revisions
        if r == revisions[0]:
            pass
        else:
            raise Exception(r)
        return (p.get_cur_revision(), su.bash.run("pwd").stdout.strip())

    with pytest.raises(Exception) as exc_info:
        local_gitgame_repo.for_each_revision(action, revisions, errors="error")

    assert exc_info.value.args[0] == revisions[1]
