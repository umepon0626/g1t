from g1t.core.utils import find_repository
from g1t.core.object import find_object, read_object, checkout_tree
from pathlib import Path


def cmd_checkout(commit: str, path: Path) -> None:
    repo = find_repository()
    obj = read_object(repo, find_object(repo, commit))
    if obj.fmt == b"commit":
        obj = read_object(repo, obj.kvlm[b"tree"].decode("ascii"))
    path.mkdir(parents=True, exist_ok=True)
    checkout_tree(repo, obj, path)
