import dataclasses
import logging
import re
import subprocess

from typing import Optional, Dict, List
import yaml

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)

BLACKLISTED_SNAP_NAMES_REGEX_PATTERNS = [
    "^core[0-9]*",
    "^bare$",
    "^snapd$",
]


@dataclasses.dataclass
class Snap:
    name: str
    version: str
    rev: str
    tracking: str
    publisher: str
    notes: str


def get_installed_snaps():
    LOG.debug("Gathering installed snaps")
    # Run snap list command to get a list of installed snaps
    result = subprocess.run("snap list", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Parse the output to extract snap names
    installed_snaps = []
    blacklisted_snaps = []
    lines = result.stdout.strip().split("\n")
    for line in lines[1:]:  # Skip the header line
        snap_info = line.split()
        if len(snap_info) >= 2:
            snap_name, version, rev, tracking, publisher, notes = snap_info[:6]
            if not any(re.match(pattern, snap_name) for pattern in BLACKLISTED_SNAP_NAMES_REGEX_PATTERNS):
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
            else:
                blacklisted_snaps.append(snap_name)
    LOG.debug(f"Found {len(installed_snaps)} installed snaps")
    LOG.debug(f"Blacklisted snaps: {', '.join(blacklisted_snaps)}")
    installable_snaps = [snap for snap in installed_snaps if "+git" not in snap.version]
    return installable_snaps


# Snap Config class
@dataclasses.dataclass
class SnapConfig(BaseConfig):
    snaps: List[Snap] = dataclasses.field(default_factory=list)

    def gather(self):
        LOG.debug("Gathering SnapConfig")
        self.snaps = get_installed_snaps()

    def generate_cloud_config(self) -> Dict:
        return {
            "snap": {
                "commands": [
                    f"snap install {snap.name}" + (" --classic" if snap.notes == "classic" else "")
                    for snap in self.snaps
                ]
            },
        }
