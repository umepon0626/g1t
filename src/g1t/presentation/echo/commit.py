from g1t.presentation.dto import CommitDto


def echo_commit(commit: CommitDto) -> None:
    print(f"Author: {commit.author}")
    print(f"Committer: {commit.committer}")
    print(f"Tree: {commit.tree}")
    print(f"Parent: {commit.parent}")
