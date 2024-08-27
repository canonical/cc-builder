import logging
import subprocess
import time
import yaml
from typing import Optional, Dict, List

from not_cloud_init.custom_types import BaseConfig
from not_cloud_init.modules.apt import AptConfig
from not_cloud_init.modules.hostname import HostnameConfig
from not_cloud_init.modules.snap import SnapConfig
from not_cloud_init.modules.ssh import SSHConfig
from not_cloud_init.modules.user import UserConfig
from not_cloud_init.console_output import print_debug, print_error, print_module_header, print_warning, print_info


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
    disabled_configs: Dict[str, bool] = {},
    rename_to_ubuntu_user: bool = False,
    **kwargs,
):
    # get current user
    if rename_to_ubuntu_user:
        current_user = "ubuntu"
    else:
        result = subprocess.run("whoami", shell=True, stdout=subprocess.PIPE, text=True)
        current_user = result.stdout.strip()

    print_debug("Initializing all not-cloud-init modules")

    configs: List[BaseConfig] = []

    if "apt" not in disabled_configs:
        configs.append(AptConfig())
    else:
        print_debug("Apt config disabled")
    if "snap" not in disabled_configs:
        configs.append(SnapConfig())
    else:
        print_debug("Snap config disabled")
    if "ssh" not in disabled_configs:
        configs.append(SSHConfig(current_user=current_user, gather_public_keys=gather_public_keys))
    else:
        print_debug("SSH config disabled")
    if "user" not in disabled_configs:
        configs.append(UserConfig(name=current_user, plaintext_password=password))
    else:
        print_debug("User config disabled")

    # enable optional modules
    if hostname_enabled:
        configs.append(HostnameConfig())

    cloud_config: Dict = {}

    print_info("Gathering data for each not-cloud-init module", ignore_quiet=True)
    for config in configs:
        # gather data for each config
        config.gather()
        # generate dict representing cloud config yaml for each config
        cc_dict = config.generate_cloud_config()
        # if the user config already exists, merge it with the new user config
        if "users" in cc_dict and "users" in cloud_config:
            cloud_config["users"][0] = {**cloud_config["users"][0], **cc_dict["users"][0]}
            del cc_dict["users"]
        # merge cc_dict into cloud_config
        cloud_config.update(cc_dict)

    if "user" not in disabled_configs and cloud_config.get("users") and cloud_config["users"][0].get("shell") == "/usr/bin/zsh":
        if not "zsh" in cloud_config.get("packages", []):
            print_debug("User has zsh as shell, so adding zsh to list of packages.")
            cloud_config["packages"].append("zsh")

    print_info("Done gathering data for all not-cloud-init modules", ignore_quiet=True)

    with open(f"{output_path}", "w") as f:
        f.write("#cloud-config\n")

    with open(f"{output_path}", "a") as f:
        yaml_str = yaml.dump(cloud_config, default_flow_style=False, width=200)
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

    print_info(f"Wrote cloud-init config to file: {output_path}", ignore_quiet=True)
