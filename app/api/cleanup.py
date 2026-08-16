from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.post("/cleanup", include_in_schema=False)
def cleanup():
    # Uploads are already removed in /scan finally; endpoint reserved for future jobs.
    return {"status": "ok"}
