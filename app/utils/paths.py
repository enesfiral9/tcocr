from pathlib import Path
from uuid import uuid4
from app.config import TEMP_DIR, DEBUG_DIR


def create_job_paths(debug: bool = False) -> tuple[str, Path, Path | None]:
    job_id = uuid4().hex
    temp = TEMP_DIR / job_id
    temp.mkdir(parents=True, exist_ok=False)
    debug_path = DEBUG_DIR / job_id if debug else None
    if debug_path:
        debug_path.mkdir(parents=True, exist_ok=False)
    return job_id, temp, debug_path
