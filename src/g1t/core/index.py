from g1t.core.object import Repository
import math
from dataclasses import dataclass


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
