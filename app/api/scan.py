import asyncio
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from app import config
from app.logger import logger
from app.services.cleanup_service import cleanup_job
from app.services.scan_service import ScanService, summarize
from app.utils.paths import create_job_paths

router = APIRouter(prefix="/api")


@router.post("/scan")
async def scan(request: Request, file: UploadFile = File(...)):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in config.ALLOWED_EXTENSIONS or file.content_type not in config.ALLOWED_MIME_TYPES:
        raise HTTPException(415, "Yalnızca PDF, JPG, JPEG ve PNG dosyaları kabul edilir.")
    if not request.app.state.ocr.ready:
        raise HTTPException(503, "OCR engine is not ready.")
    lock = request.app.state.scan_lock
    if lock.locked():
        raise HTTPException(409, "Sistem şu anda başka bir belge işliyor. Lütfen mevcut işlemin tamamlanmasını bekleyin.")
    _, job_dir, debug_dir = create_job_paths(config.DEBUG_OCR)
    source = job_dir / f"source{extension}"
    size = 0
    try:
        async with lock:
            with source.open("wb") as destination:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                        raise HTTPException(413, "Dosya boyutu sınırı aşıldı.")
                    destination.write(chunk)
            logger.info("scan started; document accepted; bytes=%s", size)
            service = ScanService(request.app.state.ocr)
            documents = await asyncio.to_thread(service.scan, source, debug_dir)
            logger.info("scan completed; pages=%s", len(documents))
            return {"documents": [item.model_dump() for item in documents], "summary": summarize(documents)}
    finally:
        await file.close()
        cleanup_job(job_dir)
