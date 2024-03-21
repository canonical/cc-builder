import dataclasses
from typing import Optional


@dataclasses.dataclass
class BaseConfig:
    def generate_cloud_config(self):
        raise NotImplementedError()

    def gather(self):
        raise NotImplementedError()
