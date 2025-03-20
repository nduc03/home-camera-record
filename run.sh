#!/bin/bash

source ./venv_linux/bin/activate
source .env

python ./record.py $RTSP_URL1 "/camera-records" &

python ./record.py $RTSP_URL2 "/camera-records" &

wait
