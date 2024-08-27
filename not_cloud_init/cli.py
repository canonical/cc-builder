import logging
import os

import rich_click as click

from not_cloud_init.generator import create_cloud_init_config
from not_cloud_init.logger import configure_logging, set_console_to_verbose
from not_cloud_init.console_output import set_quiet_mode

LOG = logging.getLogger()

@click.command()
@click.pass_context
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Enable quiet output. Only critical errors and essential information will be displayed.", 
)
@click.option(
    "-o",
    "--output-path",
    default="cloud-config.yaml",
    help="Path to output file.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Write over output file if it already exists.",
)
@click.option(
    "--gather-hostname",
    is_flag=True,
    default=False,
    help="Enable gathering the hostname of the machine. This is will cause issues unless this exact machine is being redeployed using the generated cloud-init config.",
)
@click.option(
    "--gather-public-keys",
    is_flag=True,
    help="Enable gathering of all public key files in the ~/.ssh directory. This will allow you to use the same public keys on the new machine as the current machine.",
    default=False,
)
@click.option(
    "--password",
    help="Set the password for the user. WARNING: This is incredibly insecure and is stored in plaintext in the cloud-init config.",
    required=False,
)
@click.option(
    "--disable-apt",
    is_flag=True,
    help="Disable the gathering and generation of apt config.",
    default=False,
)
@click.option(
    "--disable-snap",
    is_flag=True,
    help="Disable the gathering and generation of snap config.",
    default=False,
)
@click.option(
    "--disable-ssh",
    is_flag=True,
    help="Disable the gathering and generation of ssh config.",
    default=False,
)
@click.option(
    "--disable-user",
    is_flag=True,
    help="Disable the gathering and generation of user config.",
    default=False,
)
@click.option(
    "--rename-to-ubuntu-user",
    is_flag=True,
    help="Keep the current user but rename it to the default 'ubuntu' user.",
    default=False,
)
# add -h as a shortcut for --help
@click.help_option("-h", "--help")
@click.version_option()
def cli(
    ctx,
    quiet,
    output_path,
    force,
    gather_hostname,
    gather_public_keys,
    password,
    disable_apt,
    disable_snap,
    disable_ssh,
    disable_user,
    rename_to_ubuntu_user,
):
    """
    Generate a cloud-init configuration file for the current machine.
    """

    configure_logging()

    if quiet:
        set_quiet_mode(True)

    if os.path.exists(f"{output_path}") and not force:
        LOG.warning(f"Output file {output_path} already exists. Use --force or -f to allow writing over existing file")
        return

    disabled_configs = []
    if disable_apt:
        disabled_configs.append("apt")
    if disable_snap:
        disabled_configs.append("snap")
    if disable_ssh:
        disabled_configs.append("ssh")
    if disable_user:
        disabled_configs.append("user")

    create_cloud_init_config(
        output_path,
        hostname_enabled=gather_hostname,
        gather_public_keys=gather_public_keys,
        password=password,
        disabled_configs=disabled_configs,
        rename_to_ubuntu_user=rename_to_ubuntu_user,
    )


def main():
    cli(obj={})

if __name__ == "__main__":
    main()
