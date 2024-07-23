from g1t.core.repository import Repository
from g1t.core.object import G1tCommit, find_object


def get_active_branch(repo: Repository) -> str | None:
    with open(repo.gitdir / "HEAD", "r") as f:
        head = f.read()

    if head.startswith("ref: refs/heads/"):
        return head.split("refs/heads/")[1].strip()
    else:
        return None


def create_new_branch(repo: Repository, new_branch_name: str) -> None:
    heads_dir = repo.gitdir / "refs" / "heads"
    branch_path = heads_dir / new_branch_name
    current_commit_sha = find_object(repo, "HEAD", G1tCommit)
    if current_commit_sha is None:
        raise Exception("HEAD is not pointing to a commit")
    try:
        branch_path.touch(exist_ok=False)
        branch_path.write_text(current_commit_sha)
    except Exception as e:
        raise Exception(f"Failed to create branch {new_branch_name}") from e


def change_head_pointing_ref(repo: Repository, branch_name: str) -> None:
    head_path = repo.gitdir / "HEAD"
    heads_dir = repo.gitdir / "refs" / "heads"
    branch_path = heads_dir / branch_name
    if branch_path.exists():
        head_path.write_text(f"ref: {branch_path.relative_to(repo.gitdir)}")
    else:
        raise Exception("branch doesn't exist")
