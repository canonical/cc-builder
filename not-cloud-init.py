import dataclasses
import os
import re
import subprocess
from pprint import pprint
from typing import Optional
import re
import subprocess
from pprint import pprint

VERBOSE = False
# VERBOSE = True


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


def deb822_to_one_line(deb822_repo, naive=True):
    if naive:
        repo_line = ""
        # repo_line += deb822_repo["types"].split()[0] + " "
        repo_line += "deb "
        repo_line += deb822_repo["uris"] + " "
        repo_line += deb822_repo["suites"] + " "
        repo_line += deb822_repo["components"]
        return repo_line
    else:
        raise NotImplementedError("Intelligent deb822 -> one line conversion not implemented yet")


def get_deb822_apt_repositories():
    # for new deb-822 format for sources.list.d
    sources_list_d_path = "/etc/apt/sources.list.d/"
    deb822_repos = []
    for filename in os.listdir(sources_list_d_path):
        if filename.endswith(".sources"):
            file_path = os.path.join(sources_list_d_path, filename)
            with open(file_path, "r") as sources_file:
                relevant_lines = [
                    l for l in sources_file.readlines() if l.split(":")[0] in ("Types", "URIs", "Suites", "Components")
                ]
                parsed_repo = {l.split(":")[0].lower(): l.split(":", maxsplit=1)[1].strip() for l in relevant_lines}
                deb822_repos.append(
                    AptRepository(
                        original_repo_line=None,
                        repo_line_without_options=deb822_to_one_line(parsed_repo),
                        name=filename.replace(".sources",".list"),
                        archive_type=None,
                        options=None,
                        uri=parsed_repo["uris"],
                        suite=parsed_repo["suites"],
                        components=parsed_repo["components"].split(),
                    )
                )
    return deb822_repos


# deb822_sources = get_deb822_apt_repositories()
# for deb822_source in deb822_sources:
#     print(deb822_to_one_line(deb822_source))


def get_apt_repositories() -> list[AptRepository]:
    # APT configuration files
    sources_list_path = "/etc/apt/sources.list"
    sources_list_d_path = "/etc/apt/sources.list.d/"

    repositories = []

    # sources_list = []
    # # Read main sources.list
    # with open(sources_list_path, "r") as sources_list_file:
    #     for line in sources_list_file:
    #         if line.startswith("deb"):
    #             sources_list.append(parse_repository_line(line.strip()))
    # print(f"{len(sources_list)} repositories found in file: {sources_list_path}")
    # pprint([repo.__dict__ for repo in sources_list])
    # repositories += sources_list

    sources_list_d = []
    # # Read files in sources.list.d directory
    for filename in os.listdir(sources_list_d_path):
        file_path = os.path.join(sources_list_d_path, filename)
        if filename.endswith(".list"):
            with open(file_path, "r") as sources_list_d_file:
                for line in sources_list_d_file:
                    if line.startswith("deb"):
                        sources_list_d.append(parse_repository_line(line.strip(), file_path=file_path))
        # new deb-822 format for sources.list.d
        elif filename.endswith(".sources"):
            with open(file_path, "r") as sources_list_d_file:
                for line in sources_list_d_file:
                    if line.startswith("deb"):
                        sources_list_d.append(parse_repository_line(line.strip(), file_path=file_path))
    print(f"{len(sources_list_d)} repositories found in directory: {sources_list_d_path}")
    repositories += sources_list_d

    return repositories


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

def get_installed_apt_packages_from_dpkg():
    # Run dpkg -l command to get a list of installed packages
    result = subprocess.run("dpkg -l", shell=True, stdout=subprocess.PIPE, text=True)

    # Parse the output to extract package names
    installed_packages = []
    lines = result.stdout.strip().split("\n")
    for line in lines[5:]:  # Skip the header lines
        package_info = line.split()
        if len(package_info) >= 2:
            package_name = package_info[1]
            installed_packages.append(package_name)

    return installed_packages


def get_installed_apt_packages_from_apt_mark():
    result = subprocess.run("apt-mark showmanual", shell=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip().split("\n")


def get_installed_packages_from_log(log_file):
    try:
        result = subprocess.run(f"zgrep 'Commandline: apt' {log_file}", shell=True, stdout=subprocess.PIPE, text=True)
        packages = []
        for line in result.stdout.strip().split("\n"):
            if re.findall(r"Commandline: apt(-get)? install ", line):
                parsed_packages = [
                    item for item in line.split("install", maxsplit=1)[1].split() if not item.startswith("-")
                ]
                packages += parsed_packages
        packages.sort()
    except subprocess.CalledProcessError:
        packages = []
        print(f"No {log_file} found")
    else:
        print(f"Found {len(packages)} packages in {log_file}")

    return packages


def get_installed_apt_packages_from_history():
    packages1 = get_installed_packages_from_log("/var/log/apt/history.log")
    packages2 = get_installed_packages_from_log("/var/log/apt/history.log.*.gz")

    packages = packages1 + packages2

    # now filter out any packages that don't exist in apt mark list
    apt_mark_packages = get_installed_apt_packages_from_apt_mark()
    actually_installed_packages = list(set([package for package in packages if package in apt_mark_packages]))
    print(f"Filtered out {len(packages) - len(actually_installed_packages)} packages using apt-mark showmanual")
    actually_installed_packages.sort()
    return actually_installed_packages


def gather():
    # Return the results
    return {
        "AptPackages": {
            "packages_dpkg": get_installed_apt_packages_from_dpkg(),
            "packages_apt_mark": get_installed_apt_packages_from_apt_mark(),
            "packages_apt_history": get_installed_apt_packages_from_history(),
        }
    }


# result = gather()
print("=======================================================================================")
print("===================================== Bad Methods =====================================")
print("=======================================================================================")
packages_dpkg = get_installed_apt_packages_from_dpkg()
print("Number of packages returned by `dpkg -l`:", len(packages_dpkg))
if VERBOSE:
    print(packages_dpkg)
packages_apt_mark = get_installed_apt_packages_from_apt_mark()
print("Number of packages returned by `apt-mark showmanual`:", len(packages_apt_mark))
if VERBOSE:
    print(packages_apt_mark)
print("================================ My Best Current Method ===============================")
packages_apt_history = get_installed_apt_packages_from_history()
print("Number of packages found in apt history:", len(packages_apt_history))
print(packages_apt_history)

"""
Exmaple output from `snap list`:
Name                      Version                     Rev    Tracking       Publisher          Notes
bare                      1.0                         5      latest/stable  canonical✓         base
chromium                  119.0.6045.159              2695   latest/stable  canonical✓         -
snapd                     2.60.4                      20290  latest/stable  canonical✓         snapd
ubuntu-bug-triage         2023.11.16+git92f6808       231    latest/stable  powersj            -
"""

import dataclasses


@dataclasses.dataclass
class Snap:
    name: str
    version: str
    rev: str
    tracking: str
    publisher: str
    notes: str


def get_installed_snaps():
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
    print(f"Filtered out {len(git_snaps)} snaps with +git in the version")
    # filter out snapd from installable snaps
    installable_snaps = [snap for snap in installable_snaps if snap.name != "snapd"]
    return installable_snaps


# Example usage
installed_snaps = get_installed_snaps()
print("Installed Snaps:")
for snap in installed_snaps:
    print(snap)


#######################################################################################################################
#######################################################################################################################
############################################## Generate cloud-init config #############################################
#######################################################################################################################
#######################################################################################################################


import yaml

apt_repos: list[AptRepository] = get_deb822_apt_repositories() + get_apt_repositories()


def generate_apt_packages_cloud_config(packages: list[str], apt_repos: list[AptRepository]):
    cloud_config = {
        "apt": {
            "sources": {
                repo.name: {"source": repo.repo_line_without_options} for repo in apt_repos if repo.name != "UNKNOWN"
            }
        },
        "packages": [package for package in packages],
    }

    return cloud_config


apt_packages_mark = get_installed_apt_packages_from_apt_mark()
apt_packages_history = get_installed_apt_packages_from_history()
apt_mark_cloud_config = generate_apt_packages_cloud_config(apt_packages_mark, apt_repos)
apt_history_cloud_config = generate_apt_packages_cloud_config(apt_packages_history, apt_repos)

# create cloud init yaml for installing snaps in the form:
"""
snap:
  commands:
    - snap install snap1
    - snap install snap2
"""


def generate_snaps_cloud_config(snaps: list[Snap]):
    cloud_config = {
        "snap": {
            "commands": [
                f"snap install {snap.name}" + (" --classic" if snap.notes == "classic" else "") for snap in snaps
            ]
        },
    }

    return cloud_config


snap_packages = get_installed_snaps()
snap_cloud_config = generate_snaps_cloud_config(snap_packages)

outputs = {
    "cloud_config_apt_mark": [apt_mark_cloud_config, snap_cloud_config],
    "cloud_config_apt_history": [apt_history_cloud_config, snap_cloud_config],
}

os_version_metadata = subprocess.run("cat /etc/os-release", shell=True, stdout=subprocess.PIPE, text=True).stdout
os_version_metadata = "OS Release & Version Info: (from /etc/os-release):\n" + os_version_metadata

for output_name, cloud_config_list in outputs.items():
    with open(f"{output_name}.yaml", "w") as f:
        f.write("#cloud-config\n")

    for cloud_config in cloud_config_list:
        with open(f"{output_name}.yaml", "a") as f:
            yaml.dump(cloud_config, f, default_flow_style=False)
            f.write

    with open(f"{output_name}.yaml", "a") as f:
        f.write("\n\n")
        f.write("#" * 80 + "\n")
        lines = ["# " + line for line in os_version_metadata.splitlines(keepends=True)]
        f.writelines(lines)
        f.write("#" * 80 + "\n")
