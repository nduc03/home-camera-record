if ! git pull; then
    echo "git pull failed, trying git pull --rebase"
    git pull --rebase
fi
chmod +x run.sh setup.sh
./setup.sh
sudo systemctl restart record-camera.service
