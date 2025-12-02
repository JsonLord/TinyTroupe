import os
import logging
from datetime import datetime

loggers = {}

def get_logger(agent_name):
    if agent_name in loggers:
        return loggers[agent_name]

    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Find the next available integer for the log file
    i = 0
    while True:
        log_file_name = os.path.join(log_dir, f"{agent_name}_{today}_{i}.log")
        if not os.path.exists(log_file_name):
            break
        i += 1

    # Set up the logger
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if this function is called multiple times for the same agent
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.FileHandler(log_file_name, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    loggers[agent_name] = logger
    return logger

def setup_agent_logger(agent_name, log_file):
    """
    Sets up a logger for a specific agent that writes to a dedicated log file.
    """
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_file) for h in logger.handlers):
        return logger

    # Clear existing handlers to ensure a clean setup
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    loggers[agent_name] = logger
    return logger
