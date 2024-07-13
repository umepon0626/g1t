from g1t.core.repository import Repository


def get_active_branch(repo: Repository) -> str | None:
    with open(repo.gitdir / "HEAD", "r") as f:
        head = f.read()

    if head.startswith("ref: refs/heads/"):
        return head.split("refs/heads/")[1].strip()
    else:
        return None
