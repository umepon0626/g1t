from g1t.core.repository import Repository
from pathlib import Path


def find_repository(path: Path = Path(".")) -> Repository:
    path = path.resolve()
    if (path / ".g1t").is_dir():
        return Repository(path)
    parent = path.parent
    if parent == path:
        raise Exception("No git directory.")
    return find_repository(parent)
