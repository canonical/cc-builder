import logging
import subprocess
import time
from pprint import pprint

import yaml

from custom_types import BaseConfig
from modules.apt import AptConfig
from modules.hostname import HostnameConfig
from modules.snap import SnapConfig
from modules.ssh import SSHConfig
from modules.user import UserConfig

LOG = logging.getLogger(__name__)

#######################################################################################################################
#######################################################################################################################
############################################## Generate cloud-init config #############################################
#######################################################################################################################
#######################################################################################################################


def create_cloud_init_config(
    output_path: str,
    hostname_enabled: bool = False,
    gather_public_keys: bool = False,
    password: str = None,
    **kwargs,
):
    # get current user
    result = subprocess.run("whoami", shell=True, stdout=subprocess.PIPE, text=True)
    current_user = result.stdout.strip()

    LOG.info("Initializing all not-cloud-init modules")
    configs: list[BaseConfig] = [
        AptConfig(),
        SnapConfig(),
        SSHConfig(gather_public_keys=gather_public_keys),
        UserConfig(plaintext_password=password),
    ]
    # enable optional modules
    if hostname_enabled:
        configs.append(HostnameConfig())

    cloud_config: dict = {}

    LOG.info("Gathering data for each not-cloud-init module")
    for config in configs:
        # gather data for each config
        config.gather()
        # generate dict representing cloud config yaml for each config
        cc_dict = config.generate_cloud_config()
        # merge cc_dict into cloud_config_sections
        cloud_config.update(cc_dict)

    if cloud_config["users"][0]["shell"] == "/usr/bin/zsh":
        if "zsh" in cloud_config["packages"]:
            LOG.debug("User has zsh as shell, but zsh already in list of packages.")
        else:
            LOG.debug("User has zsh as shell, so adding zsh to list of packages.")
            cloud_config["packages"].append("zsh")

    LOG.info(f"Writing cloud-init config to file: {output_path}")
    with open(f"{output_path}", "w") as f:
        f.write("#cloud-config\n")

    with open(f"{output_path}", "a") as f:
        yaml_str = yaml.dump(cloud_config, default_flow_style=False)
        yaml_str = yaml_str.replace("$USER", current_user)
        f.write(yaml_str)
        f.write("\n")

    # leave lil footer at the end of the file
    with open(f"{output_path}", "a") as f:
        f.write("\n")
        f.write("#" * 80 + "\n")
        # add timestamp to end of file
        f.write(f"# File created at: {time.ctime()}\n")
        f.write("# Cloud config created by not-cloud-init tool written by @a-dubs.\n")
        f.write("#" * 80 + "\n")
