from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas import ExportRequest
from app.services.excel_service import create_excel

router = APIRouter(prefix="/api")


@router.post("/export")
def export(payload: ExportRequest):
    filename = f"kimlik_ocr_{datetime.now():%Y-%m-%d_%H%M}.xlsx"
    return StreamingResponse(create_excel(payload.records), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})
