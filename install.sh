#!/bin/bash

# Clone the repository using HTTPS
echo "Cloning the repository..."
git clone https://github.com/a-dubs/not-cloud-init.git
cd not-cloud-init

# update apt
sudo apt update -y

# install pip
sudo apt install python3-pip -y

# Install python3-venv if not already installed
echo "Installing python3-venv if not already installed..."
sudo apt-get install -y python3-venv

# Create and activate a virtual environment
echo "Creating and activating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if the CLI is working
echo "Checking if CLI is working..."
python src/cli.py --help

echo "Installation complete."
