from g1t.presentation.dto import TreeDto


def echo_tree(tree: TreeDto) -> None:
    for entry in tree.entries:
        print(f"{entry.mode} {entry.object_type} {entry.sha} {entry.path}")
