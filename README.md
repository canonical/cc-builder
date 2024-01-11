# not-cloud-init

A tool for gathering information about a currently running machine and generating a basic cloud-config that can be used as a good starting point for re-creating the original machine via cloud-init.  
Since this tool only generates a cloud-config file for cloud-init to use, this tool is inherently limited by cloud-init capabilities.

A tool for gathering information about a currently running machine and generating a basic cloud-config that can be used as a good starting point for re-creating the original machine via cloud-init.
## Current State: _work in progress_ (Alpha 1.0)

I am looking to test out the reliability and robustness of the tool in its current state.

Only 2447 more stars until we surpass canonical/cloud-init 😈😈😈

## Capabilities:

- [x] Apt sources (.list files) from sources.list.d/ 
  - [x] Gather from system
  - [x] Export into cloud config
- [ ] Apt sources from sources.list
  - [x] Gather from system
  - [ ] Export into cloud config
- [x] Deb822 Apt Sources (.sources files) from sources.list.d/
  - [x] Gather from system
  - [x] Export into cloud config
- [x] Snaps installed on system
  - [x] Gather from system
  - [x] Export into cloud config
- [x] "Manually" installed apt packages (using aptmark showmanual)
  - [x] Gather from system
  - [x] Export into cloud config
- [x] Detailed operating system info 
  - [x] Gather from system
  - [x] Export into cloud config (in "commented out" metadata footer of cloud config)



## What does it do?

This tool gathers information from your system then generates two cloud config files: 
- one with apt packages from aptmark showmanual
- one with apt packages from custom apt history parsing

## Gathering feedback

If you have a few minutes to kill, please consider running this tool locally on your system or machine(s) of your
choosing. 

1. Download the not-cloud-init.py script using wget or curl:  
`wget https://raw.githubusercontent.com/a-dubs/not-cloud-init/main/not-cloud-init.py`  
or  
`curl https://raw.githubusercontent.com/a-dubs/not-cloud-init/main/not-cloud-init.py -o not-cloud-init.py`

2. Run the not-cloud-init python script:  
`python3 not-cloud-init.py`

3. Look over the content of the generated cloud-config files and then fill out this google form with your feedback
and optionally include the generated cloud-config files in the form as well if you are comfortable with doing so.
https://forms.gle/XjBJbqFtaG1svf1S8  

If you end up testing on multiple machines, you can just fill out the form multiple times and just skip to the second
page of the form to submit the cloud-config files. 


## Submitting Issues Via GitHub
In addition to the feedback form, feel free to open an issue against this repo for any bugs or features you'd like to see addressed. 

Thanks! 

