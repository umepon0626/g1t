from g1t.core.object import G1tTree
from g1t.presentation.dto import TreeDto, TreeLeafDto
from g1t.consts import MODE_OBJECT_MAP


def convert_tree(tree: G1tTree) -> TreeDto:
    return TreeDto(
        entries=[
            TreeLeafDto(
                mode=leaf.mode.decode("utf-8"),
                object_type=MODE_OBJECT_MAP[leaf.mode],
                sha=leaf.sha,
                path=leaf.path,
            )
            for leaf in tree.items
        ]
    )
