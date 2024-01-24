import dataclasses
from custom_types import BaseConfig
import subprocess
import logging

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class Snap:
    name: str
    version: str
    rev: str
    tracking: str
    publisher: str
    notes: str


def get_installed_snaps():
    LOG.info("Gathering installed snaps")
    # Run snap list command to get a list of installed snaps
    result = subprocess.run("snap list", shell=True, stdout=subprocess.PIPE, text=True)
    # Parse the output to extract snap names
    installed_snaps = []
    lines = result.stdout.strip().split("\n")
    for line in lines[1:]:  # Skip the header line
        snap_info = line.split()
        if len(snap_info) >= 2:
            snap_name, version, rev, tracking, publisher, notes = snap_info[:6]
            installed_snaps.append(
                Snap(
                    name=snap_name,
                    version=version,
                    rev=rev,
                    tracking=tracking if tracking != "-" else None,  # replace "-" with None
                    publisher=publisher if publisher != "-" else None,  # replace "-" with None
                    notes=notes if notes != "-" else None,  # replace "-" with None
                )
            )
    # find all snaps with +git in the version
    git_snaps = [snap for snap in installed_snaps if "+git" in snap.version]
    installable_snaps = [snap for snap in installed_snaps if "+git" not in snap.version]
    # filter out snapd from installable snaps
    installable_snaps = [snap for snap in installable_snaps if snap.name != "snapd"]
    return installable_snaps


# Snap Config class
@dataclasses.dataclass
class SnapConfig(BaseConfig):
    snaps: list[Snap] = dataclasses.field(default_factory=get_installed_snaps)
    
    def generate_cloud_config(self) -> dict:
        return {
            f"snap": {
                "commands": [
                    f"snap install {snap.name}" + (" --classic" if snap.notes == "classic" else "") for snap in self.snaps
                ]
            },
        }