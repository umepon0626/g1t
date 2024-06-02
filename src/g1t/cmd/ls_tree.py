from g1t.core.utils import find_repository
from g1t.core.object import find_object, read_object, G1tTree, Repository
from pathlib import Path


def cmd_ls_tree(tree: str, recursive: bool) -> None:
    repo = find_repository()
    ls_tree(repo, tree, recursive, Path("."))


def ls_tree(repo: Repository, tree: str, recursive: bool, path: Path) -> None:
    sha = find_object(repo, tree)
    obj: G1tTree = read_object(repo, sha)
    for leaf in obj.items:
        if len(leaf.mode) == 5:
            obj_type_b = leaf.mode[0:1]
        else:
            obj_type_b = leaf.mode[0:2]
        obj_type = ""

        match obj_type_b:
            case "04":
                obj_type = "tree"
            case "10":
                obj_type = "blob"  # regular file
            case "12":
                obj_type = "blob"  # symlink
            case "16":
                obj_type = "commit"  # submodule
            case _:
                raise Exception(f"Unknown object type {obj_type_b}")

        if recursive or obj_type == "tree":
            ls_tree(repo, leaf.sha, recursive, path / leaf.path)
        else:
            print(f"{obj_type} {leaf.sha} {leaf.path}")
