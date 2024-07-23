from g1t.cmd import cmd_create_branch
from pathlib import Path
from git import Repo

PROJECT_ROOT = Path(__file__).parent.parent.parent


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
