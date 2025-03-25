import configparser
import os
import logging
import sys
import shutil
from typing import Tuple

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

LINUX_CONF_PATH = '/etc/camera-records.conf'
WINDOWS_CONF_PATH = './camera-records.conf'

CONF_PATH = LINUX_CONF_PATH if sys.platform.startswith("linux") else WINDOWS_CONF_PATH

def get_storage_bytes(max_storage_str: str) -> int:
    """
    Convert the max_storage string to bytes.
    - The string can be in the format of "100M" or "1G".
    - If the format is not recognized, default to 10G.
    """
    if max_storage_str[-1] == 'M':
        return int(max_storage_str[:-1]) * 1024 ** 2
    if max_storage_str[-1] == 'G':
        return int(max_storage_str[:-1]) * 1024 ** 3
    return 10 * 1024 ** 3

def check_file(path: str) -> Tuple[bool, str]:
    """
    Check if the file exists and is writable.

    :param path: The path to the file
    :return: True if the file exists and is writable, False otherwise and also return reason
    """
    if not os.path.exists(path):
        return False, f"[ERROR] File not found: {path}"
    if not os.path.isfile(path):
        return False, f"[ERROR] Not a file: {path}"
    if not os.access(path, os.W_OK):
        return False, f"[ERROR] File is not writable: {path}"
    return True, "File OK."

if sys.platform.startswith("linux") and not os.path.exists(LINUX_CONF_PATH):
    logging.error('[ERROR] Config file not found')
    print('Config file not found')
    sys.exit(1)
elif sys.platform.startswith("win") and not os.path.exists(WINDOWS_CONF_PATH):
    if os.path.exists('conf.default'):
        shutil.copyfile('conf.default', WINDOWS_CONF_PATH)
    else:
        logging.error("[ERROR] Default config file not found. Exiting.")
        print("Default config file not found. Exiting.")
        sys.exit(1)


config = configparser.ConfigParser()

writable, reason = check_file(CONF_PATH)

if not writable:
    logging.error(reason)
    print(reason)
    sys.exit(1)

config.read(CONF_PATH)

SAVE_DIR = config.get('general', 'save_dir') if sys.platform.startswith("linux") else './videos'
max_storage = config.get('general', 'max_storage', fallback='10G') if sys.platform.startswith("linux") else '5M'
MAX_STORAGE_BYTES = get_storage_bytes(max_storage)
