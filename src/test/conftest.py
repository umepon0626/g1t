import pytest
import shutil
from typing import Generator
from pathlib import Path
from git import Repo


def pytest_configure() -> None:
    pytest.PROJECT_ROOT = Path(__file__).parent.parent.parent
    pytest.GIT_USER_NAME = "test user"
    pytest.GIT_USER_EMAIL = "test@gmail.com"

    repo = Repo(pytest.PROJECT_ROOT)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", pytest.GIT_USER_NAME)
        cw.set_value("user", "email", pytest.GIT_USER_EMAIL)


def clean_up_after_each_tests() -> None:
    # .gitフォルダを削除
    shutil.rmtree(".git")


def clean_up_after_all_tests() -> None:
    # .gitファイルを元の場所に戻す
    shutil.copytree("test/.git", ".git", dirs_exist_ok=True)


def setup_before_all_tests() -> None:
    # config設定

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
