from pathlib import Path
from g1t.core.utils import find_repository
from g1t.core.branch import create_new_branch, change_head_pointing_ref


def cmd_create_branch(branch_name: str) -> None:
    repository = find_repository(Path("."))
    create_new_branch(repository, branch_name)
    # change HEAD to the created branch
    change_head_pointing_ref(repository, branch_name)
