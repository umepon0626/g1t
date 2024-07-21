from g1t.cmd.add import cmd_add
from pathlib import Path
from git import Repo, IndexEntry


PROJECT_ROOT = Path(__file__).parent.parent.parent
SAMPLE_FILE_PATH = PROJECT_ROOT / "sample.txt"


def add_test_sample_file() -> None:
    with open(SAMPLE_FILE_PATH, "w") as f:
        f.write("Hello, World!")


def delete_added_file() -> None:
    repo = Repo(PROJECT_ROOT)
    try:
        repo.index.remove([SAMPLE_FILE_PATH])
    except:
        pass
    SAMPLE_FILE_PATH.unlink()


def compare_two_indexed_files(
    original_files: list[IndexEntry], g1t_files: list[IndexEntry]
) -> None:
    assert len(original_files) == len(g1t_files)
    for original_entry, g1t_entry in zip(original_files, g1t_files):
        assert original_entry.path == g1t_entry.path
        assert original_entry.hexsha == g1t_entry.hexsha


def test_add() -> None:
    add_test_sample_file()
    repo = Repo(PROJECT_ROOT)
    repo.index.add([SAMPLE_FILE_PATH])
    original_git_indexed_files = [b[1] for b in repo.index.entries.items()]

    delete_added_file()

    add_test_sample_file()

    cmd_add([SAMPLE_FILE_PATH])
    g1t_indexed_files = [b[1] for b in repo.index.entries.items()]

    compare_two_indexed_files(original_git_indexed_files, g1t_indexed_files)
