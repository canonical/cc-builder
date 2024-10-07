import dataclasses
import socket

from cc_builder.console_output import print_debug, print_error, print_info, print_module_header, print_warning
from cc_builder.custom_types import BaseConfig


def get_hostname():
    hostname = socket.gethostname()
    print_debug(f"Found hostname: {hostname}")
    return hostname


@dataclasses.dataclass
class HostnameConfig(BaseConfig):
    hostname: str = None

    def gather(self):
        self.hostname = get_hostname()

    def generate_cloud_config(self):
        return {
            "hostname": self.hostname,
        }
