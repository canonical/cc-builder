import dataclasses
from typing import Optional


import dataclasses

@dataclasses.dataclass
class BaseConfig:
    
    def generate_cloud_config(self):
        raise NotImplementedError()
