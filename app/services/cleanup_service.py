import shutil
from pathlib import Path
from app.logger import logger


def cleanup_job(path: Path) -> None:
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        logger.info("temporary files removed")
