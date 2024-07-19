import pytest
import shutil
from typing import Generator


def clean_up_after_each_tests() -> None:
    # .gitフォルダを削除
    shutil.rmtree(".git")


def clean_up_after_all_tests() -> None:
    # .gitファイルを元の場所に戻す
    shutil.copytree("test/.git", ".git", dirs_exist_ok=True)


def setup_before_all_tests() -> None:
    # .gitファイルを別の場所にコピー
    shutil.copytree(".git", "test/.git", dirs_exist_ok=True)


def setup_before_each_tests() -> None:
    # .gitファイルをもとに戻す
    shutil.copytree("test/.git", ".git", dirs_exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def secure_original_git_folder() -> Generator[None, None, None]:
    setup_before_all_tests()
    yield
    clean_up_after_all_tests()


@pytest.fixture(scope="function", autouse=True)
def reset_git_folder() -> Generator[None, None, None]:
    setup_before_each_tests()
    yield
    clean_up_after_each_tests()
