import os
from pathlib import Path
from g1t.core.repository import Repository
from g1t.core.index import read_index
from g1t.core.object import read_object, G1tBlob
from fnmatch import fnmatch


ContentsAndIgnoreFlag = tuple[str, bool]


class G1tIgnore(object):
    scoped: dict[str, list[ContentsAndIgnoreFlag]] | None = None
    global_ignore: dict[str, list[ContentsAndIgnoreFlag]] | None = None

    def __init__(
        self,
        scoped: dict[str, list[ContentsAndIgnoreFlag]],
        global_ignore: list[list[ContentsAndIgnoreFlag]],
    ) -> None:
        self.scoped = scoped
        self.global_ignore = global_ignore


def ignore_parse_one_line(raw_line: str) -> ContentsAndIgnoreFlag | None:
    line = raw_line.strip()
    if len(line) == 0 | line.startswith("#"):
        return None

    if line.startswith("!"):
        return line[1:], False

    if line[0] == "\\":
        return line[1:], True

    return line, True


def parse_git_ignore(lines: list[str]) -> list[ContentsAndIgnoreFlag]:
    ret: list[ContentsAndIgnoreFlag] = []

    for line in lines:
        parsed = ignore_parse_one_line(line)
        if parsed is not None:
            ret.append(parsed)

    return ret


def read_all_gitignore_config(repo: Repository):
    ignore = G1tIgnore(scoped=dict(), global_ignore=[])
    local_config = repo.gitdir / "info/exclude"
    if local_config.exists():
        with open(local_config) as f:
            ignore.global_ignore.append(parse_git_ignore(f.readlines()))

    global_config = Path.home() / ".config"
    if "XDG_CONFIG_HOME" in os.environ:
        global_config = Path(os.environ["XDG_CONFIG_HOME"])
    global_config = global_config / "g1t" / "ignore"
    if global_config.exists():
        with open(global_config) as f:
            ignore.global_ignore.append(parse_git_ignore(f.readlines()))

    ignore.global_ignore.append([(".git/**", True)])

    # TODO: why does we read .gitignore from index file?
    index = read_index(repo)
    for entry in index.entries:
        if entry.name == ".gitignore" or entry.name.endswith("/.gitignore"):
            obj: G1tBlob = read_object(repo, entry.sha)
            lines = obj.blobdata.decode("utf8").splitlines()
            ignore.scoped[os.path.dirname(entry.name)] = parse_git_ignore(lines)

    return ignore


def is_target_ignored(
    rules: list[ContentsAndIgnoreFlag], target_path: Path
) -> bool | None:
    result = None
    for pattern, value in rules:
        if fnmatch(str(target_path), pattern):
            result = value

        # NOTE: search for directories.
        if result is None and (not pattern.endswith("*")):
            if fnmatch(str(target_path), pattern + "/**"):
                result = value
    return result


def check_ignore_scoped(
    rules_for_ignoring: list[ContentsAndIgnoreFlag], target_path: Path
):
    parent = target_path.parent

    while True:
        if parent.name in rules_for_ignoring:
            result = is_target_ignored(rules_for_ignoring[parent.name], target_path)
            if result is not None:
                return result

        if len(parent.name) == 0:
            break
        parent = parent.parent
    return None


def check_ignore_not_scoped(rules_for_ignoring: list[str], target_path: Path) -> bool:
    parent = target_path.parent
    for rule in rules_for_ignoring:
        result = is_target_ignored(rule, parent)
        if result is not None:
            return result
    return False


def check_ignore(rules: G1tIgnore, target_path: Path) -> bool:
    if check_ignore_scoped(rules.scoped, target_path):
        return True
    return check_ignore_not_scoped(rules.global_ignore, target_path)
