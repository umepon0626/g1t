from g1t.core.repository import Repository
from g1t.core.object import find_object, read_object
from pathlib import Path
import os
import configparser


def find_repository(path: Path = Path(".")) -> Repository:
    path = path.resolve()
    if (path / ".git").is_dir():
        return Repository(path)
    parent = path.parent
    if parent == path:
        raise Exception("No git directory.")
    return find_repository(parent)


def tree_to_dict(repo: Repository, tree_ref: str, prefix: Path) -> dict[str, str]:
    dst = {}
    sha = find_object(repo, tree_ref, fmt=b"tree")
    if sha is None:
        raise Exception(f"Not a tree object {tree_ref}")
    tree = read_object(repo, sha)

    for item in tree.items:
        path = prefix / item.path
        is_subtree = item.mode.startswith(b"04")
        if is_subtree:
            dst.update(tree_to_dict(repo, item.sha, path))
        else:
            dst[str(path.relative_to(repo.worktree))] = item.sha
    return dst


def read_gitconfig() -> configparser.ConfigParser:
    xdg_config_home = (
        os.environ["XDG_CONFIG_HOME"]
        if "XDG_CONFIG_HOME" in os.environ
        else "~/.config"
    )
    configfiles = [
        os.path.expanduser(os.path.join(xdg_config_home, "git/config")),
        os.path.expanduser("~/.gitconfig"),
    ]

    config = configparser.ConfigParser()
    config.read(configfiles)
    return config


def get_user_from_gitconfig(config: configparser.ConfigParser) -> str | None:
    if "user" in config:
        if "name" in config["user"] and "email" in config["user"]:
            return "{} <{}>".format(config["user"]["name"], config["user"]["email"])
    return None
