from pathlib import Path
from configparser import ConfigParser


class Repository:
    def __init__(self, path: Path, check_dir_exist: bool = False) -> None:
        self.worktree = path
        self.gitdir = path / ".git"

        if check_dir_exist and not self.gitdir.is_dir():
            raise Exception(f"Not a git repository {path}")

        config_parser = ConfigParser()
        config_file = self.gitdir / "config"
        if config_parser and config_file.exists():
            config_parser.read(config_file)
            if check_dir_exist:
                raise Exception(f"Config file missing {config_file}")
