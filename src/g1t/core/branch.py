from g1t.core.repository import Repository
from g1t.core.object import G1tCommit, find_object, G1tBlob
from g1t.core.utils import tree_to_dict
from pathlib import Path

TreeDiff = dict[str, tuple[str | None, str | None]]


def get_active_branch(repo: Repository) -> str | None:
    with open(repo.gitdir / "HEAD", "r") as f:
        head = f.read()

    if head.startswith("ref: refs/heads/"):
        return head.split("refs/heads/")[1].strip()
    else:
        return None


def create_new_branch(repo: Repository, new_branch_name: str) -> None:
    heads_dir = repo.gitdir / "refs" / "heads"
    branch_path = heads_dir / new_branch_name
    current_commit_sha = find_object(repo, "HEAD", G1tCommit)
    if current_commit_sha is None:
        raise Exception("HEAD is not pointing to a commit")
    try:
        branch_path.touch(exist_ok=False)
        branch_path.write_text(current_commit_sha)
    except Exception as e:
        raise Exception(f"Failed to create branch {new_branch_name}") from e


def change_head_pointing_ref(repo: Repository, branch_name: str) -> None:
    head_path = repo.gitdir / "HEAD"
    heads_dir = repo.gitdir / "refs" / "heads"
    branch_path = heads_dir / branch_name
    if branch_path.exists():
        head_path.write_text(f"ref: {branch_path.relative_to(repo.gitdir)}")
    else:
        raise Exception("branch doesn't exist")


def tree_diff(repo: Repository, a_sha: str, b_sha: str) -> TreeDiff:
    a_tree = tree_to_dict(repo, a_sha, Path())
    b_tree = tree_to_dict(repo, b_sha, Path())
    all_paths = set(a_tree.keys()) | set(b_tree.keys())
    diff = {}
    for path in all_paths:
        a_blob_sha = a_tree.get(path, None)
        b_blob_sha = b_tree.get(path, None)
        if a_blob_sha != b_blob_sha:
            diff[path] = (a_blob_sha, b_blob_sha)
    return diff


def apply_changes(repo: Repository, change: TreeDiff) -> None:
    for path, (a_sha, b_sha) in change.items():
        if a_sha is None and b_sha is None:
            raise Exception(f"Both sha are None for {path}")
        elif b_sha is None:
            delete_file(repo, path)
        elif a_sha is None:
            create_new_file(repo, path, b_sha)
        else:
            delete_file(repo, path)
            create_new_file(repo, path, b_sha)


def create_new_file(repo: Repository, path: str, sha: str) -> None:
    obj = find_object(repo, sha, G1tBlob)
    if isinstance(obj, G1tBlob):
        with open(repo.worktree / path, "wb") as f:
            f.write(obj.blobdata)


def delete_file(repo: Repository, path: str) -> None:
    (repo.worktree / path).unlink()
