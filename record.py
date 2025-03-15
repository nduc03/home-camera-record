import ffmpeg
import os
import time
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
    DEBUG = True
except ImportError:
    DEBUG = False

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
        :param max_storage: Maximum storage limit in GB before deleting old files
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

    #! bug Inconsistent calculation from different threads
    def _get_seconds_until_next_split(self) -> int:
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
        return int((next_split - now).total_seconds())

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
        """Continuously record the video and split files at each new hour/minute."""
        while True:
            # Get current timestamp and calculate duration until next split
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            duration = self._get_seconds_until_next_split()
            filename = self.save_dir / f"{self.ip_addr}_{timestamp}.mp4"

            print(f"[INFO] Recording: {filename} (Duration: {duration} sec, DEBUG={DEBUG})")

            # Use ffmpeg-python to start recording
            try:
                (
                    ffmpeg
                    .input(self.rtsp_url, rtsp_transport="udp", hwaccel="auto")
                    .output(str(filename), vcodec="copy", acodec="aac", t=duration)
                    .run(overwrite_output=True)
                )
            except ffmpeg.Error as e:
                print(f"[ERROR] FFmpeg Error: {e}")

if __name__ == "__main__":
    store_size = 20 * (1024 ** 2) if DEBUG else 10 * (1024 ** 3)
    recorder1 = RTSPRecorder(
        rtsp_url=os.getenv("RTSP_URL1"),
        save_dir=f"./videos/{extract_ip(os.getenv("RTSP_URL1"))}",
        max_storage_bytes=store_size
    )
    recorder2 = RTSPRecorder(
        rtsp_url=os.getenv("RTSP_URL2"),
        save_dir=f"./videos/{extract_ip(os.getenv("RTSP_URL2"))}",
        max_storage_bytes=store_size
    )
    record1_thread = threading.Thread(target=recorder1.record_stream)
    record2_thread = threading.Thread(target=recorder2.record_stream)

    record1_thread.start()
    record2_thread.start()

    record1_thread.join()
    record2_thread.join()
