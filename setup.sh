# Install necessary packages
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg

# Create a virtual environment and install the necessary libraries
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install service
## Replaces %s with the current directory in the record-camera.service file
CURRENT_DIR=$(pwd)
cp record-camera.service.template record-camera.service
sed -i "s|%s|$CURRENT_DIR|g" "record-camera.service"
## Copy the service file to the systemd directory
sudo mv record-camera.service /etc/systemd/system/
## Start the service
sudo systemctl daemon-reload
sudo systemctl enable record-camera.service
sudo systemctl start record-camera.service