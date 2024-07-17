from g1t.cmd import cat_file
from g1t.core.object import G1tCommit
from pathlib import Path
from git import Repo

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_cat_commit() -> None:
    commit_sha = "3aa49bb4e0df176968ea00255420767b8634ce81"
    obj = cat_file.cmd_cat_file(commit_sha)
    assert isinstance(obj, G1tCommit)
    repo = Repo(PROJECT_ROOT)
    commit = repo.commit(commit_sha)

    assert obj.kvlm[b"tree"] == commit.tree.hexsha.encode()
    assert obj.kvlm[b"parent"] == commit.parents[0].hexsha.encode()
    assert obj.kvlm[b"author"].decode().startswith(commit.author.name)
    assert obj.kvlm[b"committer"].decode().startswith(commit.committer.name)
