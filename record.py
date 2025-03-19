import ffmpeg
import os
import time
import threading
import uuid
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
    DEBUG = True
except ImportError:
    DEBUG = False

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

def extract_ip(rtsp_url: str) -> str:
    """
    Extracts the IP address from an RTSP URL.

    :param rtsp_url: The RTSP URL (e.g., rtsp://user:pass@192.168.1.95:8554/profile0)
    :return: The extracted IP address as a string
    """
    parsed_url = urlparse(rtsp_url)
    host = parsed_url.hostname
    return host if host else "unknown_" + str(uuid.uuid4())

class RTSPRecorder:
    def __init__(self, rtsp_url: str, save_dir: str, max_storage_bytes: int = 1024 ** 3):
        """
        Initialize the RTSP Recorder.

        :param rtsp_url: RTSP stream URL of the camera
        :param save_dir: Directory to store recorded files
        :param max_storage: Maximum storage limit in byte before deleting old files
        """
        self.rtsp_url = rtsp_url
        self.save_dir = Path(save_dir)
        self.max_storage_bytes = max_storage_bytes

        self.ip_addr = extract_ip(rtsp_url)

        # Ensure save directory exists
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # Start file deletion thread
        self.cleanup_thread = threading.Thread(target=self._delete_old_files, daemon=True)
        self.cleanup_thread.start()

    @staticmethod
    def get_seconds_until_next_split() -> int:
        """
        Calculate the seconds remaining until the next split point (hourly or minutely).
        - If DEBUG is True → Split every minute
        - If DEBUG is False → Split every hour
        """
        now = datetime.now()
        if not DEBUG:
            next_split = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        else:
            next_split = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        result = int((next_split - now).total_seconds())
        if result < 1:
            return result + 60 if DEBUG else result + 3600
        return result

    def _get_total_storage_used(self) -> float:
        """Get total storage used by video files in GB."""
        total_size = sum(f.stat().st_size for f in self.save_dir.glob("*.mp4"))
        return total_size


    def _delete_old_files(self):
        """Continuously check and delete old files if storage exceeds the limit."""
        while True:
            while self._get_total_storage_used() > self.max_storage_bytes:
                oldest_file = sorted(self.save_dir.glob("*.mp4"), key=os.path.getctime)[0]
                print(f"[INFO] Deleting old file: {oldest_file}")
                os.remove(oldest_file)
            time.sleep(60)  # Check storage every 60 seconds

    def record_stream(self):
        """
        Record the camera and split files at every new hour/minute.
        The record will drop if connection is hang for more than 30 seconds.
        """
        while True:
            # Get current timestamp and calculate duration until next split
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            duration = RTSPRecorder.get_seconds_until_next_split()
            filename = self.save_dir / f"{self.ip_addr}_{timestamp}_fragmented.mp4"

            logging.info(f"[INFO] Recording: {filename} (Duration: {duration} sec, DEBUG={DEBUG})")
            print(f"[INFO] Recording: {filename} (Duration: {duration} sec, DEBUG={DEBUG})")

            # Use ffmpeg-python to start recording
            try:
                (
                    ffmpeg
                    .input(self.rtsp_url, rtsp_transport="udp", hwaccel="auto", timeout="30000000")
                    .output(str(filename), vcodec="copy", acodec="aac", t=duration, movflags="frag_keyframe+empty_moov")
                    .run(quiet=True, overwrite_output=True)
                )
            except ffmpeg.Error as e:
                logging.error(f"[ERROR] FFmpeg Error: {e}")
                print(f"[ERROR] FFmpeg Error: {e}")

def check_directory(path: str) -> bool, str:
    """
    Check if the directory exists and is writable.

    :param path: The path to the directory
    :return: True if the directory exists and is writable, False otherwise and also return reason
    """
    if not os.path.exists(path):
        return False, f"[ERROR] Directory not found: {path}"
    if not os.path.isdir(path):
        return False, f"[ERROR] Not a directory: {path}"
    if not os.access(path, os.W_OK):
        return False, f"[ERROR] Directory is not writable: {path}"
    return True, "Directory OK."

if __name__ == "__main__":
    argv = sys.argv[1:]
    if len(argv) < 2:
        print("Usage: python record.py <RTSP_URL> <save_dir>")
        sys.exit(1)
    argv_rtsp_url = argv[0]
    save_dir_str = argv[1]

    # Check if the save directory is writable
    is_writable, msg = check_directory(save_dir)
    if not is_writable:
        print(msg)
        logging.error(msg)
        sys.exit(1)

    save_dir_path = Path(save_dir_str) / extract_ip(argv_rtsp_url)

    store_size = 10 * (1024 ** 2) if DEBUG else 10 * (1024 ** 3)
    recorder = RTSPRecorder(
        rtsp_url=argv_rtsp_url,
        save_dir=save_dir_path,
        max_storage_bytes=store_size
    )
    recorder.record_stream()
