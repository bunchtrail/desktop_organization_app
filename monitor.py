import time
import threading
from config_manager import load_config
from file_sorter import sort_desktop
from logger import get_logger

logger = get_logger(__name__)

def start_monitoring():
    config = load_config()
    interval = config.get("check_interval", 300)
    logger.info("Monitoring started. Checking desktop every %s seconds.", interval)
    
    def monitor_loop():
        while True:
            sort_desktop()
            time.sleep(interval)

    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    return t
