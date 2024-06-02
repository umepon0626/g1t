from g1t.core.repository import Repository
import zlib
import hashlib
from collections import OrderedDict
from pathlib import Path


class G1tObject(object):
    def __init__(self, data=None) -> None:
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    def serialize(self) -> bytes:
        raise NotImplementedError("Subclass must implement serialize method")

    def deserialize(self, data: bytes) -> None:
        raise NotImplementedError("Subclass must implement deserialize method")

    def init(self) -> None:
        pass


class G1tTreeLeaf(object):
    def __init__(self, mode, path: str, sha) -> None:
        self.mode = mode
        self.path = path
        self.sha = sha


class G1tTree(G1tObject):
    fmt = b"tree"

    def serialize(self) -> bytes:
        return super().serialize()

    def deserialize(self, data: bytes) -> bytes:
        self.items = parse_tree(data)

    def init(self) -> None:
        self.items = []


class G1tCommit(G1tObject):
    fmt = b"commit"

    def serialize(self) -> bytes:
        return serialize_kvlm(self.kvlm)

    def init(self) -> None:
        self.kvlm = dict()

    def deserialize(self, data: bytes) -> None:
        self.kvlm = parse_kvlm(data)


class G1tBlob(G1tObject):
    fmt = b"blob"

    def serialize(self) -> bytes:
        return self.blobdata

    def deserialize(self, data: bytes) -> None:
        self.blobdata = data


def read_object(repository: Repository, sha: str) -> G1tObject:
    path = repository.gitdir / "objects" / sha[:2] / sha[2:]
    with path.open("rb") as f:
        raw = zlib.decompress(f.read())

        space = raw.find(b" ")
        null_byte = raw.find(b"\x00", space)
        fmt = raw[:space].decode("ascii")
        size = int(raw[space:null_byte].decode("ascii"))

        if size != len(raw) - null_byte - 1:
            raise Exception(f"Malformed object {sha}: bad length")
        if fmt == "commit":
            return G1tCommit(raw[null_byte + 1 :])
        elif fmt == "tree":
            return G1tTree(raw[null_byte + 1 :])
        # elif fmt == "tag":
        #     return Tag(raw[space + 1 :])
        if fmt == "blob" or fmt == "tree":
            return G1tBlob(raw[null_byte + 1 :])
        else:
            raise Exception(f"Unknown type {fmt}")


def write_object(obj: G1tObject, repository: Repository | None = None):
    data = obj.serialize()
    raw = obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data
    sha = hashlib.sha1(raw).hexdigest()
    if repository is not None:
        path = repository.gitdir / "objects" / sha[:2] / sha[2:]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as f:
                f.write(zlib.compress(raw))
    return sha


def hash_object(file_data, fmt: str, repo=None):
    data = file_data.read()
    match fmt:
        case "blob":
            obj = G1tBlob(data)
        case _:
            raise Exception(f"Unknown type {fmt}")
    return write_object(obj, repo)


def find_object(repo: Repository, name: str) -> str:
    return name


def parse_kvlm(raw, start=0, dct=None):
    if not dct:
        dct = OrderedDict()
    space = raw.find(b" ", start)

    new_line = raw.find(b"\n", start)
    if (space < 0) or (new_line < space):
        assert new_line == start
        dct[None] = raw[start + 1 :]
        return dct

    key = raw[start:space]
    end = start
    while True:
        end = raw.find(b"\n", end + 1)
        if raw[end + 1] != ord(" "):
            break
    value = raw[space + 1 : end].replace(b"\n ", b"\n")
    if key in dct:
        if not isinstance(dct[key], list):
            dct[key] = [dct[key]]
        dct[key].append(value)
    else:
        dct[key] = value
    return parse_kvlm(raw, start=end + 1, dct=dct)


def serialize_kvlm(kvlm: OrderedDict):
    ret = b""
    for k, v in kvlm.items():
        if k is None:
            continue
        if isinstance(v, list):
            for value in v:
                ret += k + b" " + value.replace(b"\n", b"\n ") + b"\n"
        else:
            ret += k + b" " + v.replace(b"\n", b"\n ") + b"\n"
    return ret


def parse_one_tree(raw: bytes, start=0) -> tuple[G1tTreeLeaf, int]:
    x = raw.find(b" ", start)
    assert x - start == 5 or x - start == 6

    mode = raw[start:x]
    if len(mode) == 5:
        mode = b" " + mode
    y = raw.find(b"\x00", x)
    path = raw[x + 1 : y]
    sha = format(int.from_bytes(raw[y + 1 : y + 21], "big"), "040x")
    return G1tTreeLeaf(mode, path.decode("utf-8"), sha), y + 21


def parse_tree(raw: bytes) -> list[G1tTreeLeaf]:
    pos = 0
    length = len(raw)
    ret = []
    while pos < length:
        leaf, pos = parse_one_tree(raw, pos)
        ret.append(leaf)
    return ret


def tree_leaf_sort_key(leaf: G1tTreeLeaf) -> str:
    if leaf.mode.startswith(b"10"):
        return leaf.path
    return leaf.path + "/"


def serialize_tree(tree: G1tTree) -> bytes:
    ret = b""
    for leaf in sorted(tree.items, key=tree_leaf_sort_key):
        ret += (
            leaf.mode
            + b" "
            + leaf.path.encode("utf8")
            + b"\x00"
            + (int(leaf.sha, 16)).to_bytes(20, byteorder="big")
        )
    return ret


def checkout_tree(repo: Repository, tree: G1tTree, path: Path) -> None:
    for item in tree.items:
        obj = read_object(repo, item.sha)
        dst = path / item.path
        if obj.fmt == b"tree":
            dst.mkdir(exist_ok=True)
            checkout_tree(repo, obj, dst)
        else:
            with dst.open("wb") as f:
                f.write(obj.blobdata)


def resolve_ref(repo: Repository, refname: str) -> str:
    refpath = repo.gitdir / refname
    if not refpath.exists():
        return None
    with refpath.open() as f:
        refname = f.read()[:-1]
    if refname.startswith("ref: "):
        return resolve_ref(repo, refname[5:])
    return refname


def list_ref(repo: Repository, path: Path | None = None):
    if not path:
        path = repo.gitdir / "refs"
    refs = OrderedDict()
    for ref in path.iterdir():
        if ref.is_dir():
            refs[ref.name] = list_ref(repo, ref)
        else:
            refs[ref.name] = resolve_ref(repo, str(ref.relative_to(repo.gitdir)))

    return refs
