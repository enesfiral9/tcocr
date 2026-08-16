import logging
from logging.handlers import RotatingFileHandler
from .config import BASE_DIR


def configure_logging() -> logging.Logger:
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger("identity_ocr")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler = RotatingFileHandler(log_dir / "application.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    return logger


logger = configure_logging()
