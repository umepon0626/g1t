from g1t.cmd.commit import cmd_commit
from pathlib import Path
from git import Repo
import pytest


PROJECT_ROOT = Path(__file__).parent.parent.parent
SAMPLE_FILE_PATH = PROJECT_ROOT / "sample.txt"


def add_test_sample_file() -> None:
    with open(SAMPLE_FILE_PATH, "w") as f:
        f.write("Hello, World!")


def test_commit() -> None:
    add_test_sample_file()
    repo = Repo(PROJECT_ROOT)
    repo.index.add([SAMPLE_FILE_PATH])
    parent_commit = repo.head.commit
    COMMIT_MSG = "Initial commit"
    cmd_commit(COMMIT_MSG)

    commit = repo.commit("HEAD")
    assert commit.hexsha != parent_commit.hexsha
    assert commit.message == COMMIT_MSG
    assert len(commit.parents) == 1
    assert commit.parents[0] == parent_commit
    assert commit.author.name == pytest.GIT_USER_NAME
    assert commit.author.email == pytest.GIT_USER_EMAIL
    assert commit.committer.name == pytest.GIT_USER_NAME
    assert commit.committer.email == pytest.GIT_USER_EMAIL
