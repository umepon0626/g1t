from g1t.core.utils import find_repository
from g1t.core.object import list_ref
from click import echo


def cmd_show_ref():
    repo = find_repository()
    refs = list_ref(repo)
    show_ref(refs)


def show_ref(refs, with_hash=True, prefix: str = ""):
    for k, v in refs.items():
        if isinstance(v, str):
            echo(f"{v + ' ' if with_hash else ''} {prefix+'/'if prefix else ''} {k}")
        else:
            show_ref(v, with_hash, f"{prefix}{'/' if prefix else ''}{k}")
