import logging
from config_manager import load_config

config = load_config()

logging.basicConfig(
    level=config.get("log_level", "INFO"),
    format='%(asctime)s [%(levelname)s] %(message)s',
    filename='desktop_organizer.log',
    filemode='a',
    encoding='utf-8'
)

def get_logger(name):
    return logging.getLogger(name)
