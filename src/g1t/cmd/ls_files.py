from g1t.core.utils import find_repository
from g1t.core.index import read_index

MODETYPE = {0b1000: "regular file", 0b1010: "symlink", 0b1110: "git link"}


def cmd_ls_files(verbose: bool) -> None:
    repo = find_repository()
    index = read_index(repo)
    if verbose:
        print(f"Index file format v.{index.version} ")
        print(f"containing {len(index.entries)} entries")

    for entry in index.entries:
        print(entry.name)
        if verbose:
            print(f"    {MODETYPE[entry.mode_type]} with perms: {entry.mode_perms}")
            print(f"    on blob: {entry.sha}")
            print(
                f"    created: {entry.ctime[0]}.{entry.ctime[1]}, modified: {entry.mtime[0]}.{entry.mtime[1]}"
            )
            print(f"    device: {entry.dev}, inode: {entry.ino}")
            print(f"    uid: {entry.uid}, gid: {entry.gid}")
            print(
                f"    flags: stage={entry.flag_stage}, assume_valid: {entry.flag_assume_valid}"
            )
