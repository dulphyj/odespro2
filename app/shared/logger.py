import logging


def setup_logger(name: str = "docapp") -> logging.LoggerAdapter:
    base_logger = logging.getLogger(name)
    base_logger.setLevel(logging.INFO)
    if not base_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        base_logger.addHandler(handler)
    return logging.LoggerAdapter(base_logger, {"service": name})
