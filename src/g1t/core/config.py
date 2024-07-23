import os
import configparser
from g1t.core.repository import Repository


def gitconfig_read(repo: Repository):
    xdg_config_home = (
        os.environ["XDG_CONFIG_HOME"]
        if "XDG_CONFIG_HOME" in os.environ
        else "~/.config"
    )
    configfiles = [
        os.path.expanduser(os.path.join(xdg_config_home, "git/config")),
        os.path.expanduser("~/.gitconfig"),
        os.path.expanduser(repo.gitdir / "config"),
    ]

    config = configparser.ConfigParser()
    config.read(configfiles)
    return config
