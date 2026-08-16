from pathlib import Path
import cv2
import numpy as np
from app.config import DET_MODEL_DIR, REC_MODEL_DIR, DET_MODEL_NAME, REC_MODEL_NAME


class PaddleOCRService:
    def __init__(self) -> None:
        self.ocr = None
        self.error = None

    @property
    def ready(self) -> bool:
        return self.ocr is not None

    def initialize(self) -> None:
        try:
            required = (Path(DET_MODEL_DIR), Path(REC_MODEL_DIR))
            if any(not path.is_dir() or not any(item.is_file() and item.name != ".gitkeep" for item in path.rglob("*")) for path in required):
                raise FileNotFoundError("Offline detection/recognition model directories are missing.")
            from paddleocr import PaddleOCR
            # PaddleOCR 3.x parameters; local paths prevent runtime downloads.
            self.ocr = PaddleOCR(
                text_detection_model_name=DET_MODEL_NAME,
                text_detection_model_dir=str(DET_MODEL_DIR),
                text_recognition_model_name=REC_MODEL_NAME,
                text_recognition_model_dir=str(REC_MODEL_DIR),
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        except Exception as exc:
            self.error = str(exc)
            self.ocr = None

    def recognize(self, image: np.ndarray) -> tuple[str, float]:
        if not self.ready:
            raise RuntimeError("OCR engine is not ready.")
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        result = self.ocr.predict(image)
        texts, scores = [], []
        for item in result:
            payload = getattr(item, "json", item)
            if callable(payload):
                payload = payload()
            if isinstance(payload, dict) and "res" in payload:
                payload = payload["res"]
            if isinstance(payload, dict):
                texts.extend(payload.get("rec_texts", []))
                scores.extend(float(x) for x in payload.get("rec_scores", []))
        return " ".join(texts).strip(), (sum(scores) / len(scores) if scores else 0.0)
