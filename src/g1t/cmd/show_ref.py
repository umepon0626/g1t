from g1t.core.utils import find_repository
from g1t.core.object import list_ref
from click import echo
from collections import OrderedDict


def cmd_show_ref() -> None:
    repo = find_repository()
    refs = list_ref(repo)
    show_ref(refs)


def show_ref(
    refs: OrderedDict,
    with_hash: bool = True,
    prefix: str = "",
) -> None:
    for k, v in refs.items():
        if isinstance(v, str):
            echo(f"{v + ' ' if with_hash else ''} {prefix+'/'if prefix else ''} {k}")
        else:
            show_ref(v, with_hash, f"{prefix}{'/' if prefix else ''}{k}")
