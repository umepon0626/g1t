from g1t.core.utils import find_repository, get_user_from_gitconfig
from g1t.core.index import read_index
from g1t.core.commit import tree_from_index, commit_create
from g1t.core.object import find_object, G1tCommit
from g1t.core.branch import get_active_branch
from g1t.core.config import gitconfig_read
from datetime import datetime


def cmd_commit(message: str) -> None:
    repo = find_repository()
    index = read_index(repo)
    # Create trees, grab back SHA for the root tree.
    tree = tree_from_index(repo, index)

    # Create the commit object itself
    commit = commit_create(
        repo,
        tree,
        find_object(repo, "HEAD", G1tCommit),
        get_user_from_gitconfig(gitconfig_read(repo)),
        datetime.now(),
        message,
    )

    # Update HEAD so our commit is now the tip of the active branch.
    active_branch = get_active_branch(repo)
    if active_branch:  # If we're on a branch, we update refs/heads/BRANCH
        with open(repo.gitdir / "refs/heads" / active_branch, "w") as fd:
            fd.write(commit + "\n")
    else:  # Otherwise, we update HEAD itself.
        with open(repo.gitdir / "HEAD", "w") as fd:
            fd.write("\n")
