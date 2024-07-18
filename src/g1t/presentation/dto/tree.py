from dataclasses import dataclass


@dataclass
class TreeLeafDto:
    mode: str
    object_type: str
    sha: str
    path: str


@dataclass
class TreeDto:
    entries: list[TreeLeafDto]
