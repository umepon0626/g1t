import click
from g1t.core.repository import Repository
from g1t.core.object import G1tCommit, G1tTree
from g1t import cmd
from configparser import ConfigParser
from pathlib import Path
from g1t.presentation.converter.commit import commit_converter
from g1t.presentation.converter.tree import convert_tree
from g1t.presentation.echo.commit import echo_commit
from g1t.presentation.echo.tree import echo_tree


@click.group()
def main() -> int:
    return 0


@main.command()
@click.option(
    "-a",
    "--annotate",
    is_flag=True,
    help="Annotate the commit with the tagger name and date",
    default=False,
)
@click.argument("name", type=str, required=False)
@click.argument("object_name", type=str, default="HEAD", required=False)
def tag(annotate: bool, name: str | None, object_name: str) -> int:
    cmd.tag.cmd_tag(object_name, name, annotate)
    return 0


@main.command()
def show_ref() -> int:
    cmd.show_ref.cmd_show_ref()
    return 0


@main.command()
def status() -> int:
    cmd.status.cmd_status()
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
@click.option("--verbose", is_flag=True, default=False)
def ls_files(verbose: bool) -> int:
    cmd.ls_files.cmd_ls_files(verbose)
    return 0


@main.command()
@click.argument("sha", type=str)
def cat_file(sha: str) -> int:
    obj = cmd.cat_file.cmd_cat_file(sha)
    if isinstance(obj, G1tCommit):
        dto = commit_converter(obj)
        echo_commit(dto)
    elif isinstance(obj, G1tTree):
        dto = convert_tree(obj)
        echo_tree(dto)
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


@main.command()
@click.argument("path", nargs=-1)
def check_ignore(path):
    cmd.cmd_check_ignore([Path(p) for p in path])


@main.command()
@click.argument("path", nargs=-1)
def rm(path):
    cmd.cmd_rm([Path(p) for p in path])


@main.command()
@click.argument("path", nargs=-1)
def add(path):
    cmd.cmd_add([Path(p) for p in path])


@main.command()
def commit(path):
    cmd.cmd_add([Path(p) for p in path])
