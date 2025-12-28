import gzip
import logging
import os
import shutil
import sys
from datetime import datetime


def setup_logger(name: str = "bohe-api-auto-sign", log_dir: str = "./data/logs") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_file = os.path.join(log_dir, "latest.log")
    if os.path.exists(log_file):
        mod_time = os.path.getmtime(log_file)
        date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d_%H-%M-%S')
        archive_name = f"{date_str}.log.gz"
        archive_path = os.path.join(log_dir, archive_name)

        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(log_file)


    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
     datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
