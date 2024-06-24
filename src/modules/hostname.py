import dataclasses
import logging
import socket

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)


def get_hostname():
    return socket.gethostname()


@dataclasses.dataclass
class HostnameConfig(BaseConfig):
    hostname: str = None

    def gather(self):
        LOG.debug("Gathering HostnameConfig")
        self.hostname = get_hostname()

    def generate_cloud_config(self):
        return {
            "hostname": self.hostname,
        }
