from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


@router.get("/health")
def health(request: Request):
    service = request.app.state.ocr
    return {"status": "ok" if service.ready else "initializing", "ocr_ready": service.ready,
            "detail": None if service.ready else service.error}
