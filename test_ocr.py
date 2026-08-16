import argparse
import json
from pathlib import Path
from app.ocr.paddle_service import PaddleOCRService
from app.services.scan_service import ScanService


def main():
    parser = argparse.ArgumentParser(description="Tek belge üzerinde lokal OCR pipeline testi")
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    ocr = PaddleOCRService(); ocr.initialize()
    if not ocr.ready:
        raise SystemExit(f"OCR modeli hazır değil: {ocr.error}")
    result = ScanService(ocr).scan(args.image)[0]
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
