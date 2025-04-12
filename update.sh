# Discard all local changes and pull from the remote repository
git fetch --all
git reset --hard origin/main
git clean -fd
git pull origin main --force

chmod +x run.sh setup.sh
./setup.sh
sudo systemctl deamon-reload
sudo systemctl restart record-camera.service
