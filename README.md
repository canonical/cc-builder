# not-cloud-init

A tool for gathering information about a currently running machine and generating a basic cloud-config that can be used as a good starting point for re-creating the original machine via cloud-init.  
Since this tool only generates a cloud-config file for cloud-init to use, this tool is inherently limited by cloud-init capabilities.


## Current State: _work in progress_

I am looking to test out the reliability and robustness of the tool in its current state.

## Capabilities:

- [ ] Apt sources (.list files) from sources.list.d/ 
  - [ ] Gather from system
  - [ ] Export into cloud config
- [ ] Apt sources from sources.list
  - [ ] Gather from system
  - [ ] Export into cloud config
- [ ] Deb822 Apt Sources (.sources files) from sources.list.d/
  - [ ] Gather from system
  - [ ] Export into cloud config
- [ ] Snaps installed on system

- [ ] 





## What does it do?

This tool gathers information o

## Gathering feedback

If you have a few minutes to kill, please consider running this tool locally on your system or machine(s) of your choosing. 
