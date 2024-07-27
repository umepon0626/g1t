from pathlib import Path
from g1t.core.utils import find_repository
from g1t.core.object import find_object, G1tTree
from g1t.core.branch import (
    create_new_branch,
    change_head_pointing_ref,
    get_active_branch,
    tree_diff,
    apply_changes,
    update_index,
)


def cmd_create_branch(branch_name: str) -> None:
    repository = find_repository(Path("."))
    create_new_branch(repository, branch_name)
    # change HEAD to the created branch
    change_head_pointing_ref(repository, branch_name)


def cmd_switch_branch(branch_name: str) -> None:
    repository = find_repository(Path("."))
    current_branch = get_active_branch(repository)
    if current_branch == branch_name:
        print(f"Already on {branch_name}")
        return
    if current_branch is None:
        raise Exception("HEAD is detached")
    # check if the branch exists
    branch_file = repository.gitdir / "refs" / "heads" / branch_name
    if not branch_file.exists():
        raise Exception(f"Branch {branch_name} doesn't exist")
    to_commit_sha = branch_file.read_text().strip()
    current_branch_file = repository.gitdir / "refs" / "heads" / current_branch
    from_commit_sha = current_branch_file.read_text().strip()

    to_tree_sha = find_object(repository, to_commit_sha, obj_type=G1tTree)
    from_tree_sha = find_object(repository, from_commit_sha, obj_type=G1tTree)

    if to_tree_sha is None or from_tree_sha is None:
        raise Exception("Invalid commit")

    diff = tree_diff(repository, from_tree_sha, to_tree_sha)

    apply_changes(repository, diff)
    update_index(repository, diff)
    change_head_pointing_ref(repository, branch_name)
