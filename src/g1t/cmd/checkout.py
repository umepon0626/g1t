from g1t.core.utils import find_repository
from g1t.core.object import find_object, read_object, checkout_tree, G1tCommit, G1tTree
from pathlib import Path


def cmd_checkout(commit: str, path: Path) -> None:
    repo = find_repository()
    obj_sha = find_object(repo, commit)
    if obj_sha is None:
        raise Exception(f"Commit {commit} not found")
    obj = read_object(repo, obj_sha)
    if isinstance(obj, G1tCommit):
        obj = read_object(repo, obj.kvlm[b"tree"].decode("ascii"))
    if not isinstance(obj, G1tTree):
        raise Exception(f"Commit {commit} is invalid commit")
    path.mkdir(parents=True, exist_ok=True)
    checkout_tree(repo, obj, path)
