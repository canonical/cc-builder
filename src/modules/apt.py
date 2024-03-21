import dataclasses
import logging
import os
import re
import subprocess
from typing import Optional

import yaml

from custom_types import BaseConfig

LOG = logging.getLogger(__name__)


@dataclasses.dataclass
class AptRepository:
    original_repo_line: str
    repo_line_without_options: str
    name: str
    archive_type: str
    options: Optional[dict[str, list[str]]]
    uri: str
    suite: str
    components: Optional[list[str]]


@dataclasses.dataclass
class AptPackage:
    name: str


def deb822_to_one_line(deb822_repo):
    repo_line = ""
    repo_line += "deb "
    repo_line += deb822_repo["uris"] + " "
    repo_line += deb822_repo["suites"] + " "
    repo_line += deb822_repo["components"]
    return repo_line


def get_sources_list_lines() -> list[str]:
    sources_list = []
    sources_list_path = "/etc/apt/sources.list"
    # Read main sources.list
    with open(sources_list_path, "r") as sources_list_file:
        for line in sources_list_file:
            if line.startswith("deb"):
                sources_list.append(line.strip())
    return sources_list


def parse_repository_line(line: str, file_path=None) -> AptRepository:
    # if file_path:
    # print(f"Parsing repository line from file: {file_path}")
    # Repo line format source: https://manpages.ubuntu.com/manpages/trusty/man5/sources.list.5.html
    repo_info = {}
    repo_info["original_repo_line"] = line.replace("  ", " ")  # replace double spaces with single space
    repo_info["archive_type"] = line.split()[0]
    # if options exist
    if re.findall(r"\[.*?\]", line):
        repo_info["options"] = {}
        options_str = re.findall(r"\[(.*?)\]", line)[0]
        # parse each option and add to dict
        for option in options_str.strip().split():
            key, value = option.split("=")
            # if value is comma separated, split into list
            repo_info["options"][key] = value.split(",")
        # replace options string with empty string to make parsing rest of line easier
        line = line.replace(f"[{options_str}] ", "")
    else:
        repo_info["options"] = None
    line = line.replace("  ", " ")  # replace double spaces with single space
    repo_info["repo_line_without_options"] = line
    repo_info["name"] = file_path.split("/")[-1] if file_path else "UNKNOWN"
    repo_info["uri"] = line.split()[1]
    repo_info["suite"] = " ".join(line.split()[2 : min(4, len(line.split()))])
    if len(line.split()) > 4:
        repo_info["components"] = line.split()[4:]
    else:
        repo_info["components"] = None
    return AptRepository(**repo_info)


def get_apt_repositories() -> list[str]:
    LOG.debug("Gathering apt repositories")
    sources_list_d_path = "/etc/apt/sources.list.d/"
    deb822_sources_repos = []
    apt_list_repos = []
    # # Read files in sources.list.d directory
    for filename in os.listdir(sources_list_d_path):
        file_path = os.path.join(sources_list_d_path, filename)
        # old one-line format for sources.list.d
        if filename.endswith(".list"):
            with open(file_path, "r") as apt_list_file:
                for line in apt_list_file:
                    if line.startswith("deb"):
                        # sources_list_d.append(parse_repository_line(line.strip(), file_path=file_path))
                        apt_list_repos.append(parse_repository_line(line.strip(), file_path=file_path))
        # new deb-822 format for sources.list.d
        elif filename.endswith(".sources"):
            with open(file_path, "r") as deb822_sources_file:
                relevant_lines = [
                    l
                    for l in deb822_sources_file.readlines()
                    if l.split(":")[0] in ("Types", "URIs", "Suites", "Components")
                ]
                parsed_repo = {l.split(":")[0].lower(): l.split(":", maxsplit=1)[1].strip() for l in relevant_lines}
                deb822_sources_repos.append(
                    AptRepository(
                        original_repo_line=None,
                        repo_line_without_options=deb822_to_one_line(parsed_repo),
                        name=filename.replace(".sources", ".list"),
                        archive_type=None,
                        options=None,
                        uri=parsed_repo["uris"],
                        suite=parsed_repo["suites"],
                        components=parsed_repo["components"].split(),
                    )
                )
    LOG.debug(f"Found {len(apt_list_repos)} old-style one-line repositories in sources.list.d")
    LOG.debug(f"Found {len(deb822_sources_repos)} new-style deb822 repositories in sources.list.d")
    return apt_list_repos + deb822_sources_repos


def get_simplified_apt_source_line(line: str) -> str:
    if re.findall(r"\[.*?\]", line):
        options_str = re.findall(r"\[(.*?)\]", line)[0]
        line = line.replace(f"[{options_str}] ", "")
    line = line.replace("  ", " ")  # replace double spaces with single space
    return line


def get_apt_packages():
    LOG.debug("Gathering installed apt packages")
    result = subprocess.run("apt-mark showmanual", shell=True, stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().split("\n")
    result = [AptPackage(name=line.strip()) for line in lines]
    LOG.debug(f"Found {len(result)} installed apt packages")
    return result


@dataclasses.dataclass
class AptConfig(BaseConfig):
    repos: list[AptRepository] = dataclasses.field(default_factory=list)
    packages: list[AptPackage] = dataclasses.field(default_factory=list)

    def gather(self):
        LOG.debug("Gathering AptConfig")
        self.repos = get_apt_repositories()
        self.packages = get_apt_packages()

    def generate_cloud_config(self) -> dict:
        known_sources = [repo for repo in self.repos if repo.name != "UNKNOWN"]
        return {
            "apt": {
                "sources": {repo.name: {"source": repo.repo_line_without_options} for repo in known_sources},
                "packages": [package.name for package in self.packages],
            }
        }
