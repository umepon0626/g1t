from g1t.core.object import G1tCommit
from g1t.presentation.dto import CommitDto


def commit_converter(internal: G1tCommit) -> CommitDto:
    return CommitDto(
        committer=internal.kvlm[b"committer"],
        author=internal.kvlm[b"author"],
        parent=internal.kvlm[b"parent"],
        tree=internal.kvlm[b"tree"],
    )
