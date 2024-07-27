from g1t.core.object import read_object, G1tCommit, G1tTree, G1tBlob, G1tTag
from g1t.core.utils import find_repository


def cmd_cat_file(sha: str) -> G1tBlob | G1tCommit | G1tTree:
    repository = find_repository()
    obj = read_object(repository=repository, sha=sha)
    if isinstance(obj, G1tTag):
        raise Exception("Tag object is not supported")
    return obj
