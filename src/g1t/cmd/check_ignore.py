from pathlib import Path
from g1t.core.utils import find_repository
from g1t.core.ignore import read_all_gitignore_config, check_ignore


def cmd_check_ignore(paths: list[Path]) -> None:
    repo = find_repository()
    ignore_rules = read_all_gitignore_config(repo)
    for path in paths:
        if check_ignore(ignore_rules, path):
            print(path)
