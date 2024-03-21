import logging
import os

import click

from generator import create_cloud_init_config
from logger import configure_logging

LOG = logging.getLogger(__name__)


@click.group()
@click.option(
    "--log-level",
    default="WARNING",
    help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
)
@click.pass_context
def cli(ctx, log_level):
    """CLI tool for system package management."""
    ctx.ensure_object(dict)
    ctx.obj["LOG_LEVEL"] = log_level
    configure_logging(log_level)


@cli.command()
@click.pass_context
@click.option(
    "-o",
    "--output-path",
    default="cloud-init-config.yaml",
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
    # prompt="Gather the hostname of the machine?",
    is_flag=True,
    default=False,
    help="Enable gathering the hostname of the machine. This is will cause issues unless this exact machine is being redeployed using the generated cloud-init config.",
)
# # enable gathering of private key files
# @click.option(
#     "--gather-private-keys",
#     prompt="Gather private key files?",
#     is_flag=True,
#     help="Enable gathering of private key files. Only use this if you are going to keep the generated cloud-config private since the private key will be stored in plain text within the cloud-config.",
# )
def generate(ctx, output_path, force, gather_hostname):
    if os.path.exists(f"{output_path}.yaml") and not force:
        LOG.warning(
            f"Output file {output_path}.yaml already exists. Use --force or -f to allow writing over existing file"
        )
        return

    create_cloud_init_config(
        output_path,
        hostname_enabled=gather_hostname,
    )


if __name__ == "__main__":
    cli(obj={})
