import logging
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)

log_filename = os.path.join("logs", f"tradebot_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(),
    ],
)

log = logging.getLogger("tradebot")
