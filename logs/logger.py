import logging
import os
from datetime import datetime

log_dir = "mybook.logs"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)