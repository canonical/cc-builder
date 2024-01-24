import click
from logger import configure_logging
from generator import create_cloud_init_config
import os

import logging

LOG = logging.getLogger(__name__)

@click.group()
@click.option('--log-level', default='WARNING', help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).')
@click.pass_context
def cli(ctx, log_level):
    """CLI tool for system package management."""
    ctx.ensure_object(dict)
    ctx.obj['LOG_LEVEL'] = log_level
    configure_logging(log_level)


@cli.command()
@click.pass_context
@click.option('-o', '--output-path', default='cloud-init-config.yaml', help='Path to output file.')
@click.option('-f', '--force', is_flag=True, help='Write over output file if it already exists.')
def generate(ctx, output_path, force):
    if os.path.exists(f"{output_path}.yaml") and not force:
        LOG.warning(f"Output file {output_path}.yaml already exists. Use --force or -f to allow writing over existing file")
        return
    create_cloud_init_config(output_path)


if __name__ == '__main__':
    cli(obj={})

