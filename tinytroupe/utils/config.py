import logging
from pathlib import Path
import configparser

################################################################################
# Config and startup utilities
################################################################################
_config = None

def read_config_file(use_cache=True, verbose=True) -> configparser.ConfigParser:
    global _config
    if use_cache and _config is not None:
        # if we have a cached config and accept that, return it
        return _config
    
    else:
        config = configparser.ConfigParser()

        # Hardcode the configuration values to avoid file parsing errors.
        config.add_section('OpenAI')
        config.set('OpenAI', 'API_TYPE', 'helmholtz-blablador')
        config.set('OpenAI', 'MODEL', 'alias-large')
        config.set('OpenAI', 'TOP_P', '1.0')

        # Add a dummy Logging section as it is expected by the start_logger function
        if not config.has_section('Logging'):
            config.add_section('Logging')
            config.set('Logging', 'LOGLEVEL', 'INFO')

        _config = config
        return config

def pretty_print_config(config):
    print()
    print("=================================")
    print("Current TinyTroupe configuration ")
    print("=================================")
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config.items(section):
            print(f"{key} = {value}")
        print()

def pretty_print_datetime():
    from datetime import datetime
    from datetime import timezone
    now = datetime.now()
    now_utc = now.astimezone(timezone.utc)
    print(f"Current date and time (local): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current date and time (UTC):   {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")

def pretty_print_tinytroupe_version():
    try:
        import importlib.metadata
        version = importlib.metadata.version("tinytroupe")
    except Exception:
         version = "unknown"
    print(f"TinyTroupe version: {version}")

def start_logger(config: configparser.ConfigParser):
    # create logger
    logger = logging.getLogger("tinytroupe")

    # Check if 'Logging' section exists before trying to access it
    log_level = 'INFO'
    if config.has_section('Logging'):
        log_level = config['Logging'].get('LOGLEVEL', 'INFO').upper()
    logger.setLevel(level=log_level)

    # Clear any existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Prevent propagation to avoid duplicate messages from parent loggers
    logger.propagate = False

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

def set_loglevel(log_level):
    """
    Sets the log level for the TinyTroupe logger.
    Args:
        log_level (str): The log level to set (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    """
    logger = logging.getLogger("tinytroupe")
    logger.setLevel(level=log_level)
    
    # Also update all handlers to the new log level
    for handler in logger.handlers:
        handler.setLevel(log_level)