from dataclasses import dataclass


@dataclass
class CommitDto:
    author: str
    committer: str
    tree: str
    parent: str
