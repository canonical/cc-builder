import dataclasses
import logging
import os
import subprocess
from passlib.hash import sha512_crypt

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

def get_primary_group():
    result = subprocess.run("id -gn", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()

# from: https://cloudinit.readthedocs.io/en/latest/reference/modules.html#users-and-groups
# hashed_passwd: (string) Hash of user password to be applied. 
# This will be applied even if the user is preexisting.
# To generate this hash, run: mkpasswd --method=SHA-512 --rounds=500000
def hash_password(password: str) -> str:
    # result = subprocess.run(f"mkpasswd --method=SHA-512 --rounds=500000 {password}", shell=True,
    # stdout=subprocess.PIPE, text=True)
    hash = sha512_crypt.hash(password, rounds=5000)
    return hash


@dataclasses.dataclass
class UserConfig:
    name: str = "ubuntu"
    sudo: bool = True
    shell: str = "/bin/bash"
    plaintext_password: str = None
    hashed_password: str = None

    def gather(self):
        LOG.info("Gathering UserConfig")
        self.name = get_current_user()
        self.sudo = get_sudo()
        self.shell = get_shell()
        if self.plaintext_password:
            self.hashed_password = hash_password(self.plaintext_password)

    def generate_cloud_config(self) -> dict:
        users_optional_config = {}
        if self.hashed_password:
            users_optional_config["hashed_passwd"] = self.hashed_password
            users_optional_config["lock_passwd"] = False
        return {
            "users": [
                {
                    "name": self.name,
                    "sudo": "ALL=(ALL) NOPASSWD:ALL" if self.sudo else "false",
                    "shell": self.shell,
                    **users_optional_config
                }
            ]
        }
