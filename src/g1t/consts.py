from enum import StrEnum


class ObjectType(StrEnum):
    OBJ_COMMIT = "commit"
    OBJ_TREE = "tree"
    OBJ_BLOB = "blob"
    OBJ_TAG = "tag"


MODE_OBJECT_MAP = {
    b"100644": ObjectType.OBJ_BLOB,
    b"100755": ObjectType.OBJ_BLOB,
    b"040000": ObjectType.OBJ_TREE,
}
