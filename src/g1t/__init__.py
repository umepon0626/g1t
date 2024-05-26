import click
from g1t.core.repository import Repository
from configparser import ConfigParser
from pathlib import Path


@click.group()
def main() -> int:
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
