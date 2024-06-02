import click
from g1t.core.repository import Repository
from g1t import cmd
from configparser import ConfigParser
from pathlib import Path


@click.group()
def main() -> int:
    return 0


@main.command()
@click.argument("commit", type=str)
@click.argument("path", type=Path)
def checkout(commit: str, path: Path) -> int:
    cmd.checkout.cmd_checkout(commit, path)
    return 0


@main.command()
@click.argument("tree", type=str)
@click.option("--recursive", is_flag=True)
def ls_tree(tree: str, recursive: bool) -> int:
    cmd.ls_tree.cmd_ls_tree(tree, recursive)
    return 0


@main.command()
@click.argument("type_name", type=click.Choice(["blob", "commit", "tag", "tree"]))
@click.argument("sha", type=str)
def cat_file(type_name: str, sha: str) -> int:
    cmd.cat_file.cmd_cat_file(type_name, sha)
    return 0


@main.command()
@click.argument("path", default=".")
def cmd_init(path) -> int:
    repo = Repository(
        Path(path).absolute(),
    )
    if repo.gitdir.exists():
        raise Exception(f"Path already exists {repo.gitdir}")
    else:
        repo.gitdir.mkdir(parents=True)

    (repo.gitdir / "objects").mkdir(exist_ok=True)
    (repo.gitdir / "branches").mkdir(exist_ok=True)
    (repo.gitdir / "refs" / "tags").mkdir(exist_ok=True, parents=True)
    (repo.gitdir / "refs" / "heads").mkdir(exist_ok=True, parents=True)

    with (repo.gitdir / "config").open("w") as f:
        config = repo_default_config()
        config.write(f)
    return repo


def repo_default_config():
    ret = ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret
