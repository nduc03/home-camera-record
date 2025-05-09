#!/bin/bash

sudo systemctl stop record-camera.service
sudo systemctl disable record-camera.service
sudo systemctl daemon-reload

sudo rm -f /etc/systemd/system/record-camera.service

sudo rm -f /etc/camera-records.conf

SCRIPT_DIR="$(dirname $(realpath $0))"

rm -rf "$SCRIPT_DIR"
