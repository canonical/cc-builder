import dataclasses
import os
import subprocess
from typing import Dict

from not_cloud_init.console_output import print_debug, print_error, print_module_header, print_warning, print_info
from not_cloud_init.custom_types import BaseConfig

def get_shell() -> str:
    result = subprocess.run("echo $SHELL", shell=True, stdout=subprocess.PIPE, text=True)
    shell = result.stdout.strip()
    print_debug(f"Found shell: {shell.split('/')[-1]}")
    return shell


def get_sudo(user: str) -> bool:
    result = subprocess.run("getent group sudo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    is_sudo = user in result.stdout.strip().split(":")[3].split(",")
    if not is_sudo:
        print_debug(f"User '{user}' is not in the sudo group")
    else:
        print_debug(f"User '{user}' is in the sudo group")
    return is_sudo


@dataclasses.dataclass
class UserConfig(BaseConfig):
    name: str
    sudo: bool = True
    shell: str = "/bin/bash"
    plaintext_password: str = None

    def gather(self):
        print_module_header("Gathering User Configuration")
        self.sudo = get_sudo(user=self.name)
        self.shell = get_shell()

    def generate_cloud_config(self) -> Dict:
        users_optional_config = {}
        if self.plaintext_password:
            users_optional_config = {
                "plain_text_passwd": self.plaintext_password,
                "lock_passwd": False,
            }
            print_debug(f"Adding plain text password '{self.plaintext_password}' for user '{self.name}'")
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
