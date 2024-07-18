from g1t.cmd import cat_file
from g1t.core.object import G1tCommit, G1tTree
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


def test_cat_tree() -> None:
    commit_sha = "3aa49bb4e0df176968ea00255420767b8634ce81"
    tree_sha = "24442f92933f585613384ceb6934568048085deb"
    obj = cat_file.cmd_cat_file(tree_sha)
    assert isinstance(obj, G1tTree)

    repo = Repo(PROJECT_ROOT)
    commit = repo.commit(commit_sha)
    tree = commit.tree
    assert tree.hexsha == tree_sha

    assert len(obj.items) == len(tree)

    for g1t_entry, original_entry in zip(obj.items, tree):
        assert g1t_entry.sha == original_entry.hexsha
        assert g1t_entry.path == original_entry.name
        assert g1t_entry.mode == oct(original_entry.mode)[2:].encode("utf-8").zfill(6)
