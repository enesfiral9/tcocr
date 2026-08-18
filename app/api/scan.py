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
async def scan(request: Request, files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "En az bir dosya seçilmelidir.")
    validated = []
    for file in files:
        extension = Path(file.filename or "").suffix.lower()
        if extension not in config.ALLOWED_EXTENSIONS or file.content_type not in config.ALLOWED_MIME_TYPES:
            raise HTTPException(415, "Yalnızca PDF, JPG, JPEG ve PNG dosyaları kabul edilir.")
        validated.append((file, extension))
    if not request.app.state.ocr.ready:
        raise HTTPException(503, "OCR engine is not ready.")
    lock = request.app.state.scan_lock
    if lock.locked():
        raise HTTPException(409, "Sistem şu anda başka bir belge işliyor. Lütfen mevcut işlemin tamamlanmasını bekleyin.")
    _, job_dir, debug_dir = create_job_paths(config.DEBUG_OCR)
    total_size = 0
    try:
        async with lock:
            service = ScanService(request.app.state.ocr)
            documents = []
            for document_number, (file, extension) in enumerate(validated, 1):
                source = job_dir / f"source_{document_number:04d}{extension}"
                file_size = 0
                with source.open("wb") as destination:
                    while chunk := await file.read(1024 * 1024):
                        file_size += len(chunk)
                        total_size += len(chunk)
                        if file_size > config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                            raise HTTPException(413, f"{document_number}. dosya boyutu sınırı aşıldı.")
                        destination.write(chunk)
                logger.info("document accepted; index=%s; bytes=%s", document_number, file_size)
                document_debug = debug_dir / f"document_{document_number:04d}" if debug_dir else None
                if document_debug:
                    document_debug.mkdir(parents=True, exist_ok=True)
                scanned = await asyncio.to_thread(service.scan, source, document_debug, document_number)
                documents.extend(scanned)
                source.unlink(missing_ok=True)
            logger.info("scan started; documents=%s; total_bytes=%s", len(validated), total_size)
            logger.info("scan completed; pages=%s", len(documents))
            return {"documents": [item.model_dump() for item in documents], "summary": summarize(documents)}
    finally:
        for file, _ in validated:
            await file.close()
        cleanup_job(job_dir)
