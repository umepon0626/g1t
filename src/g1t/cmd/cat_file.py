from g1t.core.object import read_object
from g1t.core.utils import find_repository
import click


def cmd_cat_file(object_type: str, sha: str) -> None:
    repository = find_repository()
    obj = read_object(repository=repository, sha=sha)
    click.echo(obj.serialize())
