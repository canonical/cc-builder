import yaml
import subprocess
from custom_types import BaseConfig
import logging
from modules.apt import AptConfig

from modules.snap import SnapConfig

LOG = logging.getLogger(__name__)

#######################################################################################################################
#######################################################################################################################
############################################## Generate cloud-init config #############################################
#######################################################################################################################
#######################################################################################################################

def create_cloud_init_config(output_path: str):

    configs: list[BaseConfig] = [
        AptConfig(),
        SnapConfig(),
    ]

    cloud_configs: list[dict] = []

    for config in configs:
        cc = config.generate_cloud_config()
        cloud_configs.append(cc)

    with open(f"{output_path}.yaml", "w") as f:
            f.write("#cloud-config\n")

    for cc in cloud_configs:
        with open(f"{output_path}.yaml", "a") as f:
            yaml.dump(cc, f, default_flow_style=False)
            f.write("\n")

    # leave lil footer at the end of the file
    with open(f"{output_path}.yaml", "a") as f:
        f.write("\n")
        f.write("#" * 80 + "\n")
        f.write("# Cloud config created by not-cloud-init tool written by @a-dubs.\n")
        f.write("#" * 80 + "\n")
