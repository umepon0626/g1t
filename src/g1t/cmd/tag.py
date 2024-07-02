from g1t.core.utils import find_repository
from g1t.core.object import create_tag, list_ref
from g1t.cmd.show_ref import show_ref


def cmd_tag(obj: str, tag_name: str | None = None, store_object: bool = False) -> None:
    repo = find_repository()
    if tag_name is not None:
        create_tag(repo, tag_name, obj, store_object)
    else:
        refs = list_ref(repo)
        show_ref(refs["tags"], with_hash=False)
