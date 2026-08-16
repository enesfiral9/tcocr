from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
APP_NAME = "T.C. Kimlik OCR"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
PDF_DPI = int(os.getenv("PDF_DPI", "300"))
CARD_WIDTH = int(os.getenv("CARD_WIDTH", "1000"))
CARD_HEIGHT = int(os.getenv("CARD_HEIGHT", "630"))
CARD_ASPECT_RATIO = CARD_WIDTH / CARD_HEIGHT
CARD_RATIO_TOLERANCE = float(os.getenv("CARD_RATIO_TOLERANCE", "0.35"))
MIN_CARD_AREA_RATIO = float(os.getenv("MIN_CARD_AREA_RATIO", "0.05"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
CONFIDENCE_SUCCESS = 0.95
CONFIDENCE_REVIEW = 0.85
TEMP_DIR = BASE_DIR / "temp"
DEBUG_DIR = BASE_DIR / "debug"
OUTPUT_DIR = BASE_DIR / "output"
MODEL_DIR = BASE_DIR / "models"
PADDLEX_CACHE_DIR = MODEL_DIR / ".paddlex-cache"
# Keep PaddleX completely inside the application tree. This prevents writes to
# a service account's home directory and makes the offline deployment portable.
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(PADDLEX_CACHE_DIR))
DET_MODEL_DIR = Path(os.getenv("DET_MODEL_DIR", str(MODEL_DIR / "detection")))
REC_MODEL_DIR = Path(os.getenv("REC_MODEL_DIR", str(MODEL_DIR / "recognition")))
OCR_LANG = os.getenv("OCR_LANG", "tr")
DET_MODEL_NAME = os.getenv("DET_MODEL_NAME", "PP-OCRv5_server_det")
REC_MODEL_NAME = os.getenv("REC_MODEL_NAME", "latin_PP-OCRv5_mobile_rec")

# Ratios are calibration defaults for the front side of the current Turkish ID.
FIELD_COORDINATES = {
    "tc_no": (0.48, 0.16, 0.94, 0.25),
    "surname": (0.48, 0.29, 0.94, 0.39),
    "name": (0.48, 0.40, 0.94, 0.51),
    "birth_date": (0.48, 0.53, 0.75, 0.63),
    "serial_no": (0.48, 0.65, 0.86, 0.75),
}

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}

for directory in (TEMP_DIR, DEBUG_DIR, OUTPUT_DIR, MODEL_DIR, PADDLEX_CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)
