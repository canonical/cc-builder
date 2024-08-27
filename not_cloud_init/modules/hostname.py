import dataclasses
import socket

from not_cloud_init.console_output import print_debug, print_error, print_module_header, print_warning, print_info
from not_cloud_init.custom_types import BaseConfig


def get_hostname():
    hostname = socket.gethostname()
    print_debug(f"Found hostname: {hostname}")
    return hostname


@dataclasses.dataclass
class HostnameConfig(BaseConfig):
    hostname: str = None

    def gather(self):
        print_module_header("Gathering Hostname Configuration")
        self.hostname = get_hostname()

    def generate_cloud_config(self):
        return {
            "hostname": self.hostname,
        }
