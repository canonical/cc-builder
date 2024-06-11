import dataclasses
import logging
import os
import subprocess

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class SSHImportIDEntry:
    key_server: str  # usually "lp" or "gh"
    username: str  # the username of the user on the key server


@dataclasses.dataclass
class SSHKeyFile:
    path: str
    content: str
    public: bool = True


def trim_ssh_key(content):
    return " ".join(content.split()[:2])


def get_ssh_import_id_entries() -> list[SSHImportIDEntry]:
    try:
        # entries in ~/.ssh/authorized_keys will contain " # ssh-import-id lp:xxx" or " # ssh-import-id gh:xxx"
        with open(os.path.expanduser("~/.ssh/authorized_keys"), "r") as authorized_keys_file:
            lines = authorized_keys_file.readlines()
        entries = []
        for line in lines:
            if "ssh-import-id" in line:
                key_server, username = line.strip().split(" ")[-1].split(":")
                if SSHImportIDEntry(key_server, username) not in entries:
                    entries.append(SSHImportIDEntry(key_server, username))
        return entries
    except FileNotFoundError:
        LOG.warning("No authorized_keys file found")
        return []


def get_authorized_keys_lines() -> list[str]:
    try:
        with open(os.path.expanduser("~/.ssh/authorized_keys"), "r") as authorized_keys_file:
            lines = [
                trim_ssh_key(l.strip())
                for l in authorized_keys_file.readlines()
                if l.strip() != "" and not l.strip().startswith("#")
            ]
        return lines
    except FileNotFoundError:
        LOG.warning("No authorized_keys file found")
        return []


# grep "^PasswordAuthentication*" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*
def is_password_authentication_disabled() -> bool:
    try:
        r = subprocess.run(
            "grep '^PasswordAuthentication no' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*",
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )
        LOG.debug(f"Password authentication status line found: {r.stdout.strip()}")
        return "no" in r.stdout
    except:
        LOG.warning("Could not determine password authentication status")
        return None


def is_root_login_disabled() -> bool:
    try:
        r = subprocess.run(
            "grep '^PermitRootLogin no' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*",
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )
        LOG.debug(f"Root login status line found: {r.stdout.strip()}")
        return "no" in r.stdout
    except:
        LOG.warning("Could not determine root login status")
        return None


def get_private_ssh_keys() -> list[str]:
    # check all files in ~/.ssh/ for private keys
    # get all files in ~/.ssh/
    # then check if they are private keys by checking the first line
    private_keys = []
    for file in os.listdir(os.path.expanduser("~/.ssh/")):
        # make sure item is a file and not a directory
        if os.path.isfile(os.path.expanduser("~/.ssh/") + file):
            with open(os.path.expanduser("~/.ssh/") + file, "r") as f:
                content = f.read()
        if "BEGIN RSA PRIVATE KEY" in content.split("\n")[0] or "BEGIN OPENSSH PRIVATE KEY" in content.split("\n")[0]:
            private_keys.append(content)
    LOG.debug(f"Found {len(private_keys)} private keys")
    return private_keys


def get_public_ssh_keys() -> list[str]:
    # check all files in ~/.ssh/ for public keys
    # get all files in ~/.ssh/
    # then check if they are public keys by checking the first line
    # all supported public key types for cloud-init:
    # rsa
    # ecdsa
    # ed25519
    # ecdsa-sha2-nistp256-cert-v01@openssh.com
    # ecdsa-sha2-nistp256
    # ecdsa-sha2-nistp384-cert-v01@openssh.com
    # ecdsa-sha2-nistp384
    # ecdsa-sha2-nistp521-cert-v01@openssh.com
    # ecdsa-sha2-nistp521
    # sk-ecdsa-sha2-nistp256-cert-v01@openssh.com
    # sk-ecdsa-sha2-nistp256@openssh.com
    # sk-ssh-ed25519-cert-v01@openssh.com
    # sk-ssh-ed25519@openssh.com
    # ssh-ed25519-cert-v01@openssh.com
    # ssh-ed25519
    # ssh-rsa-cert-v01@openssh.com
    # ssh-rsa
    # ssh-xmss-cert-v01@openssh.com
    # ssh-xmss@openssh.com
    supported_public_key_types = [
        "ssh-rsa",
    ]

    public_keys = []
    for file in os.listdir(os.path.expanduser("~/.ssh/")):
        if file == "authorized_keys":
            continue
        # make sure item is a file and not a directory
        if os.path.isfile(os.path.expanduser("~/.ssh/") + file):
            with open(os.path.expanduser("~/.ssh/") + file, "r") as f:
                content = trim_ssh_key(f.read().strip())
            is_valid = any([content.startswith(key_type) for key_type in supported_public_key_types])
            if is_valid:
                public_keys.append(SSHKeyFile(path=os.path.expanduser("~/.ssh/") + file, content=content))
    return public_keys

def replace_user_path(content, user):
    # get /home/*whatever*/ path and replace it with user
    return f"/home/{user}/" + content.split("/home/",1)[1].split("/",1)[1]

def replace_user_path(content, user):
    # get /home/*whatever*/ path and replace it with user
    return f"/home/{user}/" + content.split("/home/", 1)[1].split("/", 1)[1]


@dataclasses.dataclass
class SSHConfig(BaseConfig):
    # https://cloudinit.readthedocs.io/en/latest/reference/modules.html#ssh
    current_user: str
    authorized_keys_lines: list[str] = dataclasses.field(default_factory=list)
    disable_root: bool = True
    disable_password_authentication: bool = True
    ssh_import_id: list[SSHImportIDEntry] = dataclasses.field(default_factory=list)
    # private_ssh_keys: list[SSHKeyFile] = dataclasses.field(default_factory=list)
    public_ssh_keys: list[SSHKeyFile] = dataclasses.field(default_factory=list)
    gather_public_keys: bool = False

    def gather(self):
        LOG.info("Gathering SSHConfig")
        self.disable_root = is_root_login_disabled()
        self.disable_password_authentication = is_password_authentication_disabled()
        self.ssh_import_id = get_ssh_import_id_entries()
        self.authorized_keys_lines = get_authorized_keys_lines()
        # self.private_ssh_keys = get_private_ssh_keys()
        self.public_ssh_keys = get_public_ssh_keys()

    def generate_cloud_config(self):
        optional_config = {}
        if self.disable_root is not None:
            optional_config["disable_root"] = self.disable_root
        if self.disable_password_authentication is not None:
            optional_config["ssh_pwauth"] = not self.disable_password_authentication
        result = {
            "users": [
                {
                    "name": self.current_user,
                    "ssh_import_id": [f"{entry.key_server}:{entry.username}" for entry in self.ssh_import_id],
                    "ssh_authorized_keys": self.authorized_keys_lines,
                },
            ],
        }
        if self.gather_public_keys:
            result["write_files"] = [
                {
                    "path": replace_user_path(ssh_key.path, self.current_user),
                    "content": ssh_key.content,
                    "permissions": "0644" if ssh_key.public else "0600",
                    "owner": self.current_user,
                }
                for ssh_key in self.public_ssh_keys
            ]
        return result
