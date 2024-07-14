from g1t.core.utils import find_repository
from pathlib import Path
from g1t.core.index import rm


def cmd_rm(paths: list[Path]) -> None:
    repo = find_repository()
    rm(repo, paths)
