from g1t.core.repository import Repository
import zlib
import hashlib
from collections import OrderedDict
from pathlib import Path
import re
from dataclasses import dataclass
from typing import Type


class G1tObject(object):
    def __init__(self, data: any = None) -> None:
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    def serialize(self) -> bytes:
        # TODO: delete me. It should be implemented in presentation layer
        raise NotImplementedError("Subclass must implement serialize method")

    def deserialize(self, data: bytes) -> None:
        raise NotImplementedError("Subclass must implement deserialize method")

    def init(self) -> None:
        pass


@dataclass
class G1tTreeLeaf(object):
    mode: bytes
    path: str
    sha: str


class G1tTree(G1tObject):
    fmt = b"tree"

    def serialize(self) -> bytes:
        return serialize_tree(self)

    def deserialize(self, data: bytes) -> None:
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


class G1tTag(G1tCommit):
    fmt = b"tag"


class G1tBlob(G1tObject):
    fmt = b"blob"

    def serialize(self) -> bytes:
        return self.blobdata

    def deserialize(self, data: bytes) -> None:
        self.blobdata = data


def read_object(
    repository: Repository, sha: str
) -> G1tTree | G1tTag | G1tBlob | G1tCommit:
    path = repository.gitdir / "objects" / sha[:2] / sha[2:]
    with path.open("rb") as f:
        raw = zlib.decompress(f.read())
        space = raw.find(b" ")
        fmt = raw[:space].decode("ascii")
        null_byte = raw.find(b"\x00", space)
        size = int(raw[space:null_byte].decode("ascii"))

        if size != len(raw) - null_byte - 1:
            raise Exception(f"Malformed object {sha}: bad length")
        if fmt == "commit":
            return G1tCommit(raw[null_byte + 1 :])
        elif fmt == "tree":
            return G1tTree(raw[null_byte + 1 :])
        elif fmt == "tag":
            return G1tTag(raw[null_byte + 1 :])
        elif fmt == "blob":
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


def find_object(
    repo: Repository,
    name: str,
    obj_type: Type[G1tTree]
    | Type[G1tBlob]
    | Type[G1tCommit]
    | Type[G1tTag]
    | None = None,
    follow: bool = True,
) -> str | None:
    sha_list = resolve_object(repo, name)

    if len(sha_list) == 0:
        raise Exception(f"No such reference {name}")

    if len(sha_list) > 1:
        raise Exception(f"Ambiguous reference {name}: {sha_list}")

    sha = sha_list[0]

    while True:
        obj = read_object(repo, sha)

        # TODO: refactor this fmt conditions
        if isinstance(obj, obj_type):
            return sha

        if not follow:
            return None

        if isinstance(obj, G1tTag):
            return obj.kvlm[b"object"].decode("ascii")
        elif isinstance(obj, G1tCommit) and follow:
            return obj.kvlm[b"tree"].decode("ascii")
        else:
            return None


def resolve_object(repo: Repository, name: str) -> list[str]:
    candidates: list[str] = []
    hash_re = re.compile(r"^[0-9A-Fa-f]{4,40}$")
    if len(name.strip()) <= 0 and len(name.strip()) > 40:
        return None
    if name == "HEAD":
        return [resolve_ref(repo, "HEAD")]
    if hash_re.match(name):
        name = name.lower()
        prefix = name[:2]
        rem = name[2:]
        dir = repo.gitdir / "objects" / prefix
        for d in dir.iterdir():
            if d.name.startswith(rem):
                # user doesn't care about the full hash.
                # so we need to check with `startswith`
                candidates.append(prefix + d.name)
    tag = resolve_ref(repo, "refs/tags/" + name)
    if tag:
        candidates.append(tag)
    branch = resolve_ref(repo, "refs/heads/" + name)
    if branch:
        candidates.append(branch)
    return candidates


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
        mode = b"0" + mode
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
        if isinstance(obj, G1tTree):
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


def create_ref(repo: Repository, ref_name: str, sha):
    with open(repo.gitdir / "refs" / ref_name, "w") as fp:
        fp.write(sha + "\n")


def create_tag(repo: Repository, tag_name: str, ref, create_tag_object=False):
    sha = find_object(repo, ref, obj_type=G1tCommit)
    if not create_tag_object:
        create_ref(repo, "tags/" + tag_name, sha)

    tag = G1tTag()
    tag.kvlm = OrderedDict()
    tag.kvlm[b"object"] = sha.encode()
    tag.kvlm[b"type"] = b"commit"
    tag.kvlm[b"tag"] = tag_name.encode()
    tag.kvlm[b"tagger"] = b" ".join([b"author", b"<>", b"0", b""])
    tag.kvlm[None] = (
        b"A tag generated by G1t, which won't let you customize the message!"
    )

    tag_sha = write_object(tag, repo)
    create_ref(repo, "tags/" + tag_name, tag_sha)
