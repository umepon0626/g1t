from g1t.cmd import cmd_create_branch, cmd_switch_branch
from pathlib import Path
from git import Repo
import pytest
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent

SAMPLE_FILE_PATH = pytest.PROJECT_ROOT / "src" / "sample.txt"


def add_test_sample_file() -> None:
    with open(SAMPLE_FILE_PATH, "w") as f:
        f.write("Hello, World!")


def test_create_new_branch() -> None:
    repo = Repo(PROJECT_ROOT)
    current_commit_sha = repo.commit("HEAD").hexsha
    new_branch_name = "new_branch"
    cmd_create_branch(new_branch_name)

    assert repo.active_branch.name == new_branch_name

    with open(Path(repo.working_dir) / f".git/refs/heads/{new_branch_name}") as f:
        commit_sha = f.read()
    assert commit_sha == current_commit_sha

    with open(Path(repo.working_dir) / ".git/HEAD") as f:
        head_content = f.read()
    assert head_content == f"ref: refs/heads/{new_branch_name}"


def test_switch_to_existing_branch() -> None:
    repo = Repo(PROJECT_ROOT)
    repo.git.stash()
    new_branch_name = "new_branch"
    cmd_create_branch(new_branch_name)
    add_test_sample_file()
    # diffがあることを確認

    assert len(repo.index.diff(None)) == 1
    repo.index.add([SAMPLE_FILE_PATH])

    repo.index.commit("test commit")

    cmd_switch_branch("main")

    assert repo.active_branch.name == "main"
    assert not SAMPLE_FILE_PATH.exists()
    # statusが空であることを確認
    assert not repo.index.diff(None)
