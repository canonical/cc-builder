import logging
import os
import subprocess
import time
from io import StringIO
from typing import Dict, List

import click
import yaml
from rich.console import Console
from rich.syntax import Syntax
from ruamel.yaml import YAML

from cc_builder.console_output import print_debug, print_error, print_info, print_module_header, print_warning
from cc_builder.custom_types import BaseConfig
from cc_builder.modules.apt import AptConfig
from cc_builder.modules.hostname import HostnameConfig
from cc_builder.modules.snap import SnapConfig
from cc_builder.modules.ssh import SSHConfig
from cc_builder.modules.user import UserConfig

console = Console(color_system="auto")
LOG = logging.getLogger()

custom_yaml = YAML()
custom_yaml.width = 9999

def merge_new_config_into_existing_config(existing_config: Dict, new_config: Dict) -> Dict:
    """
    Merge a new config dict into an existing config dict.
    """
    for key, value in new_config.items():
        if key in existing_config:
            if isinstance(existing_config[key], dict) and isinstance(value, dict):
                existing_config[key] = {**existing_config[key], **value}
            elif isinstance(existing_config[key], list) and isinstance(value, list):
                existing_config[key].extend(value)
            else:
                existing_config[key] = value
        else:
            existing_config[key] = value
    return existing_config


def print_yaml_dict(yaml_dict: Dict, header: str):
    """
    Print a dictionary as YAML.
    """
    yaml_str = yaml.dump(yaml_dict, default_flow_style=False, width=200)
    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
    # print header detailing what the yaml is for (i.e. "YAML generated for user module")
    console.print(
        header,
        style="bold",
    )
    # style the console output so the background color is the default console background color
    console.print(
        syntax,
        style="on default",
    )


def create_cloud_init_config(
    output_path: str,
    interactive: bool = False,
    # hostname_enabled: bool = False,
    gather_public_keys: bool = False,
    password: str = None,
    disabled_configs: List[str] = [],
    rename_to_ubuntu_user: bool = False,
    **kwargs,
):
    # Get current user
    result = subprocess.run("whoami", shell=True, stdout=subprocess.PIPE, text=True)
    current_user = result.stdout.strip()
    original_current_user = current_user  # Keep track of original user

    # print_debug("Initializing all cc-builder modules")

    # Initialize module information
    module_info = [
        {"name": "user", "class": UserConfig, "disabled": ("user" in disabled_configs)},
        {"name": "ssh", "class": SSHConfig, "disabled": ("ssh" in disabled_configs)},
        {"name": "apt", "class": AptConfig, "disabled": ("apt" in disabled_configs)},
        {"name": "snap", "class": SnapConfig, "disabled": ("snap" in disabled_configs)},
        {"name": "hostname", "class": HostnameConfig, "disabled": ("hostname" in disabled_configs)},
    ]

    # Prepare to collect configurations
    cloud_config: Dict = {}

    if interactive:

        # Interactive mode: prompt the user for each module
        print_info("Interactive mode enabled.", ignore_quiet=True)

        # For each module, ask the user if they want to include it
        for module in module_info:
            default_gather = not module["disabled"]
            # add one line of whitespace before each module header
            console.print("")
            print_module_header(module["name"].capitalize() + " configuration")
            gather_module = click.confirm(
                f"Would you like to gather {module['name']} configuration?", default=default_gather
            )
            if gather_module:
                module["disabled"] = False

                # Gather config immediately
                if module["name"] == "ssh":
                    # For SSH module, ask about gathering public keys
                    default_public_keys = gather_public_keys
                    gather_public_keys = click.confirm(
                        "Would you like to gather public SSH keys?", default=default_public_keys
                    )
                    config = module["class"](current_user=current_user, gather_public_keys=gather_public_keys)
                elif module["name"] == "user":
                    # For User module, ask about renaming to 'ubuntu' user
                    default_rename = rename_to_ubuntu_user
                    rename_to_ubuntu_user = click.confirm(
                        "Would you like to rename the user to the default 'ubuntu' username?", default=default_rename
                    )
                    if rename_to_ubuntu_user:
                        current_user = "ubuntu"
                    else:
                        current_user = original_current_user
                    # Ask about password
                    set_password = click.confirm(
                        "Would you like to set a password for the user? WARNING: This is insecure and stored in plaintext in the cloud-init config.",
                        default=bool(password),
                    )
                    if set_password:
                        password = click.prompt("Please enter the password", hide_input=True, confirmation_prompt=True)
                    else:
                        password = None
                    config = module["class"](name=current_user, plaintext_password=password)
                else:
                    config = module["class"]()

                # Gather data for the config
                config.gather()
                # Generate dict representing cloud config yaml for the config
                cc_dict = config.generate_cloud_config()

                # Output the YAML portion generated by this module
                yaml_buffer = StringIO()
                custom_yaml.dump(
                    data=cc_dict,
                    stream=yaml_buffer,
                )
                yaml_str = yaml_buffer.getvalue()
                # remove trailing newline, otherwise a blank line at the end is rendered by rich's Syntax()
                if yaml_str[-1] == "\n":
                    yaml_str = yaml_str[:-1]
                # syntax = Syntax(yaml_str, "yaml", theme="github-dark", line_numbers=True)
                syntax = Syntax(yaml_str, "yaml", line_numbers=True)
                console.print(
                    f"[bold]YAML generated for {module['name']} module:[/bold]",
                )
                console.print(syntax)

                # If the user config already exists, merge it with the new user config
                if "users" in cc_dict and "users" in cloud_config:
                    cloud_config["users"][0] = {**cloud_config["users"][0], **cc_dict["users"][0]}
                    del cc_dict["users"]
                # Merge cc_dict into cloud_config
                cloud_config.update(cc_dict)

            else:
                module["disabled"] = True
                print_debug(f"Skipping {module['name'].capitalize()} configuration")

    else:
        # Non-interactive mode: use disabled_configs as given
        for module in module_info:
            if module["disabled"]:
                print_debug(f"{module['name'].capitalize()} config disabled")
            else:
                # Gather config
                if module["name"] == "ssh":
                    config = module["class"](current_user=current_user, gather_public_keys=gather_public_keys)
                elif module["name"] == "user":
                    config = module["class"](name=current_user, plaintext_password=password)
                else:
                    config = module["class"]()

                config.gather()
                cc_dict = config.generate_cloud_config()
                if "users" in cc_dict and "users" in cloud_config:
                    cloud_config["users"][0] = {**cloud_config["users"][0], **cc_dict["users"][0]}
                    del cc_dict["users"]
                cloud_config.update(cc_dict)

    print_info("\nDone gathering configurations for all modules", ignore_quiet=True)

    with open(f"{output_path}", "w") as f:
        f.write("#cloud-config\n\n")

    with open(f"{output_path}", "a") as f:
        individual_configs = []
        for key in cloud_config:
            individual_configs.append({key: cloud_config[key]})
        for config in individual_configs:
            yaml_buffer = StringIO()
            custom_yaml.dump(
                data=config,
                stream=yaml_buffer,
            )
            yaml_str = yaml_buffer.getvalue()
            # yaml_str = yaml_str.replace("$USER", current_user)
            f.write(yaml_str)
            f.write("\n")

    # Leave footer at the end of the file
    with open(f"{output_path}", "a") as f:
        f.write("\n")
        f.write("#" * 80 + "\n")
        # Add timestamp to end of file
        f.write(f"# File created at: {time.ctime()}\n")
        f.write("# Cloud config created by cc-builder tool (github.com/canonical/cc-builder).\n")
        f.write("#" * 80 + "\n")

    # if path already exists, print a warning
    if os.path.exists(f"{output_path}"):
        print_warning(f"Overwriting existing file: {output_path}", ignore_quiet=True)
    print_info(f"Wrote cloud-init config to file: {output_path}", ignore_quiet=True)
