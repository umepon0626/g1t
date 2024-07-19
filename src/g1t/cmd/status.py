from g1t.core.repository import Repository
from g1t.core.branch import get_active_branch
from g1t.core.ignore import read_all_gitignore_config, check_ignore
from g1t.core.utils import tree_to_dict, find_repository
from g1t.core.index import G1tIndex, read_index
from g1t.core.object import hash_object
from pathlib import Path


def cmd_status() -> None:
    repo = find_repository()
    index = read_index(repo)
    cmd_status_branch(repo)
    cmd_status_head_index(repo, index)
    cmd_status_index_worktree(repo, index)


def cmd_status_branch(repo: Repository) -> None:
    branch = get_active_branch(repo)
    if branch:
        print(f"On branch {branch}")
    else:
        print(f"HEAD detached at {repo.head}")


def cmd_status_head_index(repo: Repository, index: G1tIndex) -> None:
    print("Changes to be committed:")
    head = tree_to_dict(repo, "HEAD", repo.worktree)
    for entry in index.entries:
        if entry.name in head:
            if head[entry.name] != entry.sha:
                print(f"  (modified) {entry.name}")
            del head[entry.name]
        else:
            print(f"  (new file) {entry.name}")

    for entry in head.keys():
        print(f" (deleted) {entry}")


def cmd_status_index_worktree(repo: Repository, index: G1tIndex) -> None:
    print("Changes not staged for commit:")
    ignore = read_all_gitignore_config(repo)
    all_files: list[Path] = list()
    for root, _, files in repo.worktree.walk():
        if root == repo.gitdir:
            continue
        for f in files:
            full_path = root / f
            rel_path = full_path.relative_to(repo.worktree)
            all_files.append(rel_path)

    for entry in index.entries:
        full_path = repo.worktree / entry.name
        if not full_path.exists():
            print(f"  (deleted) {entry.name}")
        else:
            stat = full_path.stat()
            ctime_ns: int = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns: int = entry.mtime[0] * 10**9 + entry.mtime[1]
            if ctime_ns != stat.st_ctime_ns or mtime_ns != stat.st_mtime_ns:
                print(f"  (modified) {entry.name}")
                with open(full_path, "rb") as f:
                    new_sha = hash_object(f, "blob", None)
                    if entry.sha != new_sha:
                        print(f"  (modified content) {entry.name}")

        if Path(entry.name) in all_files:
            all_files.remove(Path(entry.name))

    print("Untracked files:")
    for f in all_files:
        if not check_ignore(ignore, f):
            print(f"  {f.name}")
