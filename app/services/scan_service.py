from pathlib import Path
import cv2
from app import config
from app.logger import logger
from app.schemas import DocumentResult, FieldResult
from app.ocr.card_detector import detect_identity_card
from app.ocr.card_normalizer import correct_perspective
from app.ocr.field_extractor import extract_fields, draw_field_coordinates
from app.ocr.preprocessing import field_variants, to_grayscale
from app.validators.field_normalizer import normalize_field
from app.validators.tc_validator import validate_tc_number
from app.validators.name_validator import validate_name
from app.validators.date_validator import validate_date
from .document_service import iter_document_pages


class ScanService:
    def __init__(self, ocr_service) -> None:
        self.ocr = ocr_service

    def scan(self, source: Path, debug_dir: Path | None = None) -> list[DocumentResult]:
        results = []
        for page_number, image in iter_document_pages(source):
            try:
                result = self._scan_page(page_number, image, debug_dir)
            except Exception:
                logger.exception("page %s processing failed (no personal data logged)", page_number)
                result = DocumentResult(page=page_number, failed=True, errors=["Sayfa işlenemedi."])
            results.append(result)
            logger.info("page %s processed; review=%s", page_number, result.requires_review)
            del image
        return results

    def _scan_page(self, page: int, image, debug_root: Path | None) -> DocumentResult:
        page_dir = debug_root / f"page_{page:03d}" if debug_root else None
        if page_dir:
            page_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(page_dir / "original.png"), image)
            cv2.imwrite(str(page_dir / "grayscale.png"), to_grayscale(image))
        corners, edges = detect_identity_card(image)
        if page_dir:
            cv2.imwrite(str(page_dir / "edges.png"), edges)
        if corners is None:
            return DocumentResult(page=page, failed=True, errors=["Kimlik kartı tespit edilemedi."])
        card = correct_perspective(image, corners)
        if page_dir:
            cv2.imwrite(str(page_dir / "normalized_card.png"), card)
            cv2.imwrite(str(page_dir / "detected_card.png"), card)
            cv2.imwrite(str(page_dir / "card_with_fields.png"), draw_field_coordinates(card))
        fields, confidence, invalid = self._read_card(card, page_dir)
        if invalid or confidence < config.CONFIDENCE_SUCCESS:
            rotated = cv2.rotate(card, cv2.ROTATE_180)
            rotated_fields, rotated_confidence, rotated_invalid = self._read_card(rotated, None)
            if self._quality(rotated_fields, rotated_confidence) > self._quality(fields, confidence):
                card, fields, confidence, invalid = rotated, rotated_fields, rotated_confidence, rotated_invalid
                if page_dir:
                    cv2.imwrite(str(page_dir / "normalized_card_rotated.png"), card)
        review = bool(invalid) or confidence < config.CONFIDENCE_SUCCESS
        errors = [f"{name} alanı doğrulanamadı." for name in invalid]
        return DocumentResult(page=page, **fields, overall_confidence=confidence, requires_review=review, errors=errors)

    def _read_card(self, card, page_dir: Path | None):
        crops = extract_fields(card)
        fields = {}
        validators = {"tc_no": validate_tc_number, "name": validate_name, "surname": validate_name,
                      "birth_date": validate_date, "serial_no": lambda value: bool(value) and 5 <= len(value) <= 12}
        for name, crop in crops.items():
            attempts = []
            for variant_index, processed in enumerate(field_variants(crop, numeric=name in {"tc_no", "birth_date"})):
                if page_dir:
                    cv2.imwrite(str(page_dir / f"{name}_v{variant_index + 1}.png"), processed)
                raw, confidence = self.ocr.recognize(processed)
                value = normalize_field(name, raw)
                valid = validators[name](value)
                attempts.append(FieldResult(value=value, raw_value=raw, confidence=confidence, valid=valid))
                if valid and confidence >= config.CONFIDENCE_SUCCESS:
                    break
            fields[name] = max(attempts, key=lambda item: (item.valid, item.confidence, len(item.value)))
        confidence = sum(field.confidence for field in fields.values()) / len(fields)
        invalid = [name for name, field in fields.items() if not field.valid]
        return fields, confidence, invalid

    @staticmethod
    def _quality(fields: dict[str, FieldResult], confidence: float) -> tuple[int, float, int]:
        return sum(field.valid for field in fields.values()), confidence, sum(bool(field.value) for field in fields.values())


def summarize(results: list[DocumentResult]) -> dict[str, int]:
    failed = sum(item.failed for item in results)
    review = sum(item.requires_review and not item.failed for item in results)
    return {"total": len(results), "success": len(results) - review - failed, "review": review, "failed": failed}
