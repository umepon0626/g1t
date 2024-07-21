from g1t.cmd.add import cmd_add
from pathlib import Path
from git import Repo


PROJECT_ROOT = Path(__file__).parent.parent.parent
SAMPLE_FILE_PATH = PROJECT_ROOT / "sample.txt"


def add_test_sample_file() -> None:
    with open(SAMPLE_FILE_PATH, "w") as f:
        f.write("Hello, World!")


def delete_added_file() -> None:
    repo = Repo(PROJECT_ROOT)
    repo.index.remove([SAMPLE_FILE_PATH])
    SAMPLE_FILE_PATH.unlink()


def compare_two_indexed_files(original_files, g1t_files):
    assert len(original_files) == len(g1t_files)
    for original_entry, g1t_entry in zip(original_files, g1t_files):
        assert original_entry[1] == g1t_entry[1]


def test_add() -> None:
    add_test_sample_file()
    repo = Repo(PROJECT_ROOT)
    repo.index.add([SAMPLE_FILE_PATH])
    original_git_indexed_files = [b for b in repo.index.entries.items()]

    delete_added_file()

    add_test_sample_file()

    cmd_add([SAMPLE_FILE_PATH])
    g1t_indexed_files = [b for b in repo.index.entries.items()]

    compare_two_indexed_files(original_git_indexed_files, g1t_indexed_files)
