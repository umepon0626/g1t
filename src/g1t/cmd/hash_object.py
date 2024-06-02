from g1t.core.utils import find_repository
from g1t.core.object import hash_object
from pathlib import Path


def cmd_hash_object(path: Path, write: bool = False) -> None:
    if write:
        repository = find_repository()
    else:
        repository = None
    obj = hash_object(repository, path, write)
    print(obj)
    return obj
