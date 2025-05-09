#!/bin/bash

CURRENT_USER=$(logname)
CURRENT_DIR=$(pwd)

# Install necessary packages
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg

# Create a virtual environment and install the necessary libraries
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install -r requirements.txt

# Add permissions to run.sh, update.sh
chmod +x run.sh
chmod +x update.sh

# Copy configuration file template
sudo cp camera-records.conf.default /etc/camera-records.conf

# Create a directory to store the camera records
sudo mkdir -p /camera-records
sudo chown $CURRENT_USER:$CURRENT_USER /camera-records
sudo chmod 700 /camera-records

# Create log files
sudo touch /var/log/record-camera-output.txt
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/record-camera-output.txt
sudo chmod 644 /var/log/record-camera-output.txt
sudo touch /var/log/record-camera-error.txt
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/record-camera-error.txt
sudo chmod 644 /var/log/record-camera-error.txt

# Install service
## Copy the service file template
cp record-camera.service.template record-camera.service
## Replaces variable in the service file
sed -i "s|%s|$CURRENT_DIR|g" "record-camera.service"
sed -i "s|%u|$CURRENT_USER|g" "record-camera.service"
## Move the service file to the systemd directory
sudo mv record-camera.service /etc/systemd/system/
## Start the service
sudo systemctl daemon-reload
sudo systemctl enable record-camera.service
sudo systemctl start record-camera.service
