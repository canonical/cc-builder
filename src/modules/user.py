import dataclasses
import logging
import os
import subprocess

import yaml
from passlib.hash import sha512_crypt

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)


def get_current_user() -> str:
    result = subprocess.run("whoami", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def get_shell() -> str:
    result = subprocess.run("echo $SHELL", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def get_sudo(user: str) -> bool:
    result = subprocess.run("getent group sudo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return get_current_user() in result.stdout.strip().split(":")[3].split(",")


def get_primary_group():
    result = subprocess.run("id -gn", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


@dataclasses.dataclass
class UserConfig:
    name: str
    sudo: bool = True
    shell: str = "/bin/bash"
    plaintext_password: str = None

    def gather(self):
        LOG.info("Gathering UserConfig")
        self.sudo = get_sudo(user=self.name)
        self.shell = get_shell()

    def generate_cloud_config(self) -> dict:
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
