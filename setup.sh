#!/bin/bash

# Install necessary packages
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg

# Create a virtual environment and install the necessary libraries
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install -r requirements.txt

# Install service
## Copy the service file template
cp record-camera.service.template record-camera.service
## Replaces variable in the service file
CURRENT_DIR=$(pwd)
sed -i "s|%s|$CURRENT_DIR|g" "record-camera.service"
CURRENT_USER=$(whoami)
sed -i "s|%u|$CURRENT_USER|g" "record-camera.service"
## Copy the service file to the systemd directory
sudo mv record-camera.service /etc/systemd/system/
## Start the service
sudo systemctl daemon-reload
sudo systemctl enable record-camera.service
sudo systemctl start record-camera.service