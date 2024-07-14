from g1t.core.utils import find_repository
from pathlib import Path
from g1t.core.index import add


def cmd_add(paths: list[Path]) -> None:
    repo = find_repository()
    add(repo, paths)
