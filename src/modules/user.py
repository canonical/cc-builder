import dataclasses
import logging
import os
import subprocess

import yaml

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)


def get_current_user() -> str:
    result = subprocess.run("whoami", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def get_shell() -> str:
    result = subprocess.run("echo $SHELL", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def get_sudo() -> bool:
    result = subprocess.run("getent group sudo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return get_current_user() in result.stdout.strip().split(":")[3].split(",")


@dataclasses.dataclass
class UserConfig:
    name: str = "ubuntu"
    sudo: bool = True
    shell: str = "/bin/bash"

    def gather(self):
        LOG.info("Gathering UserConfig")
        self.name = get_current_user()
        self.sudo = get_sudo()
        self.shell = get_shell()

    def generate_cloud_config(self) -> dict:
        return {
            "users": [
                {
                    "name": self.name,
                    "sudo": "ALL=(ALL) NOPASSWD:ALL" if self.sudo else "false",
                    "shell": self.shell,
                }
            ]
        }
