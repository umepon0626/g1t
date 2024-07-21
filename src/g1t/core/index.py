from g1t.core.object import Repository, hash_object
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass
class G1tIndexEntry(object):
    ctime: tuple[int, int] | None
    mtime: tuple[int, int] | None
    dev: int
    ino: int
    mode_type: int
    mode_perms: int
    uid: int
    gid: int
    fsize: int
    sha: str
    flag_assume_valid: bool
    flag_stage: bool
    name: str | None


class G1tIndex(object):
    version = None
    entries = []

    def __init__(self, version=2, entries: list[G1tIndexEntry] = None) -> None:
        if not entries:
            entries = []
        self.version = version
        self.entries = entries


def read_index(repo: Repository) -> G1tIndex:
    index_file = repo.gitdir / "index"
    if not index_file.exists():
        return G1tIndex()

    with open(index_file, "rb") as f:
        raw = f.read()

    header = raw[:12]
    signature = header[:4]
    assert signature == b"DIRC", "Invalid index file signature"
    version = int.from_bytes(header[4:8], "big")
    assert version in (2,), f"Unsupported index version {version}"
    count = int.from_bytes(header[8:12], "big")

    entries = []
    content = raw[12:]
    idx = 0
    for i in range(count):
        ctime_s = int.from_bytes(content[idx : idx + 4])
        ctime_ns = int.from_bytes(content[idx + 4 : idx + 8])

        mtime_s = int.from_bytes(content[idx + 8 : idx + 12])
        mtime_ns = int.from_bytes(content[idx + 12 : idx + 16])

        dev = int.from_bytes(content[idx + 16 : idx + 20], "big")
        # Inode
        ino = int.from_bytes(content[idx + 20 : idx + 24], "big")
        # Ignored.
        unused = int.from_bytes(content[idx + 24 : idx + 26], "big")
        assert 0 == unused
        mode = int.from_bytes(content[idx + 26 : idx + 28], "big")
        mode_type = mode >> 12
        assert mode_type in [0b1000, 0b1010, 0b1110]
        mode_perms = mode & 0b0000000111111111
        # User ID
        uid = int.from_bytes(content[idx + 28 : idx + 32], "big")
        # Group ID
        gid = int.from_bytes(content[idx + 32 : idx + 36], "big")
        # Size
        fsize = int.from_bytes(content[idx + 36 : idx + 40], "big")
        # SHA (object ID).  We'll store it as a lowercase hex string
        # for consistency.
        sha = format(int.from_bytes(content[idx + 40 : idx + 60], "big"), "040x")
        # Flags we're going to ignore
        flags = int.from_bytes(content[idx + 60 : idx + 62], "big")
        # Parse flags
        flag_assume_valid = (flags & 0b1000000000000000) != 0
        flag_extended = (flags & 0b0100000000000000) != 0
        assert not flag_extended
        flag_stage = flags & 0b0011000000000000
        # Length of the name.  This is stored on 12 bits, some max
        # value is 0xFFF, 4095.  Since names can occasionally go
        # beyond that length, git treats 0xFFF as meaning at least
        # 0xFFF, and looks for the final 0x00 to find the end of the
        # name --- at a small, and probably very rare, performance
        # cost.
        name_length = flags & 0b0000111111111111

        # We've read 62 bytes so far.
        idx += 62

        if name_length < 0xFFF:
            assert content[idx + name_length] == 0x00
            raw_name = content[idx : idx + name_length]
            idx += name_length + 1
        else:
            print("Notice: Name is 0x{:X} bytes long.".format(name_length))
            # This probably wasn't tested enough.  It works with a
            # path of exactly 0xFFF bytes.  Any extra bytes broke
            # something between git, my shell and my filesystem.
            null_idx = content.find(b"\x00", idx + 0xFFF)
            raw_name = content[idx:null_idx]
            idx = null_idx + 1

        # Just parse the name as utf8.
        name = raw_name.decode("utf8")
        idx = 8 * math.ceil(idx / 8)

        # And we add this entry to our list.
        entries.append(
            G1tIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=dev,
                ino=ino,
                mode_type=mode_type,
                mode_perms=mode_perms,
                uid=uid,
                gid=gid,
                fsize=fsize,
                sha=sha,
                flag_assume_valid=flag_assume_valid,
                flag_stage=flag_stage,
                name=name,
            )
        )
    return G1tIndex(version=version, entries=entries)


def write_index(repo: Repository, index: G1tIndex):
    with open(repo.gitdir / "index", "wb") as f:
        # Write the magic bytes.
        f.write(b"DIRC")
        # Write version number.
        f.write(index.version.to_bytes(4, "big"))
        # Write the number of entries.
        f.write(len(index.entries).to_bytes(4, "big"))

        # ENTRIES

        idx = 0
        for e in index.entries:
            f.write(e.ctime[0].to_bytes(4, "big"))
            f.write(e.ctime[1].to_bytes(4, "big"))
            f.write(e.mtime[0].to_bytes(4, "big"))
            f.write(e.mtime[1].to_bytes(4, "big"))
            f.write(e.dev.to_bytes(4, "big"))
            f.write(e.ino.to_bytes(4, "big"))

            # Mode
            mode = (e.mode_type << 12) | e.mode_perms
            f.write(mode.to_bytes(4, "big"))

            f.write(e.uid.to_bytes(4, "big"))
            f.write(e.gid.to_bytes(4, "big"))

            f.write(e.fsize.to_bytes(4, "big"))
            # @FIXME Convert back to int.
            f.write(int(e.sha, 16).to_bytes(20, "big"))

            flag_assume_valid = 0x1 << 15 if e.flag_assume_valid else 0

            name_bytes = e.name.encode("utf8")
            bytes_len = len(name_bytes)
            if bytes_len >= 0xFFF:
                name_length = 0xFFF
            else:
                name_length = bytes_len

            # We merge back three pieces of data (two flags and the
            # length of the name) on the same two bytes.
            f.write((flag_assume_valid | e.flag_stage | name_length).to_bytes(2, "big"))

            # Write back the name, and a final 0x00.
            f.write(name_bytes)
            f.write((0).to_bytes(1, "big"))

            idx += 62 + len(name_bytes) + 1

            # Add padding if necessary.
            if idx % 8 != 0:
                pad = 8 - (idx % 8)
                f.write((0).to_bytes(pad, "big"))
                idx += pad


def rm(
    repo: Repository, paths: list[Path], delete: bool = True, skip_missing: bool = False
):
    index = read_index(repo)

    # Make paths absolute
    abspaths: list[Path] = list()
    for path in paths:
        abspath = path.absolute()
        if str(abspath).startswith(str(repo.worktree)):
            abspaths.append(abspath)
        else:
            raise Exception("Cannot remove paths outside of worktree: {}".format(paths))

    kept_entries = list()
    remove = list()

    for e in index.entries:
        full_path = repo.worktree / e.name

        if full_path in abspaths:
            remove.append(full_path)
            abspaths.remove(full_path)
        else:
            kept_entries.append(e)  # Preserve entry

    if len(abspaths) > 0 and not skip_missing:
        raise Exception("Cannot remove paths not in the index: {}".format(abspaths))

    if delete:
        for path in remove:
            path.unlink()

    index.entries = kept_entries
    write_index(repo, index)


def add(repo: Repository, paths: list[Path]):
    rm(repo, paths, delete=False, skip_missing=True)

    # Convert the paths to pairs: (absolute, relative_to_worktree).
    # Also delete them from the index if they're present.
    clean_paths = list()
    for path in paths:
        abspath = path.absolute()
        if not (str(abspath).startswith(str(repo.worktree)) and abspath.is_file()):
            raise Exception("Not a file, or outside the worktree: {}".format(paths))
        relpath = abspath.relative_to(repo.worktree)
        clean_paths.append((abspath, relpath))

        # Find and read the index.  It was modified by rm.          #
        # @FIXME, though: we could just
        # move the index through commands instead of reading and writing
        # it over again.
        index = read_index(repo)

        for abspath, relpath in clean_paths:
            with open(abspath, "rb") as fd:
                sha = hash_object(fd, "blob", repo)

            stat = abspath.stat()

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = G1tIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=0b1000,
                mode_perms=0o644,
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                flag_assume_valid=False,
                flag_stage=False,
                name=relpath.name,
            )
            index.entries.append(entry)

        # Write the index back
        write_index(repo, index)
