import dataclasses
import logging
import os
import subprocess
from typing import Dict

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)


def get_shell() -> str:
    result = subprocess.run("echo $SHELL", shell=True, stdout=subprocess.PIPE, text=True)
    shell = result.stdout.strip()
    LOG.debug("Found shell: %s", shell.split("/")[-1])
    return shell


def get_sudo(user: str) -> bool:
    result = subprocess.run("getent group sudo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    is_sudo = user in result.stdout.strip().split(":")[3].split(",")
    if not is_sudo:
        LOG.debug("User '%s' is not in the sudo group", user)
    else:
        LOG.debug("User '%s' is in the sudo group", user)
    return is_sudo


@dataclasses.dataclass
class UserConfig(BaseConfig):
    name: str
    sudo: bool = True
    shell: str = "/bin/bash"
    plaintext_password: str = None

    def gather(self):
        LOG.debug("Gathering UserConfig")
        self.sudo = get_sudo(user=self.name)
        self.shell = get_shell()

    def generate_cloud_config(self) -> Dict:
        users_optional_config = {}
        if self.plaintext_password:
            users_optional_config = {
                "plain_text_passwd": self.plaintext_password,
                "lock_passwd": False,
            }
            LOG.debug("Adding plain text password '%s' for user '%s'", self.plaintext_password, self.name)
        return {
            "users": [
                {
                    "name": self.name,
                    "sudo": "ALL=(ALL) NOPASSWD:ALL" if self.sudo else None,
                    "shell": self.shell,
                    **users_optional_config,
                }
            ],
        }
