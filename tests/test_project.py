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
        clone_url=f"file://{tmp_path.absolute()}/git-game.git",
    )


@pytest.fixture
def remote_gitgame_repo():
    """The git-game repo on github."""
    return su.project.Project(
        full_name="pengyunie_git-game",
        clone_url=f"https://github.com/pengyunie/git-game.git",
    )


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
