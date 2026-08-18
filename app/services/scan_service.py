from pathlib import Path
import cv2
from app import config
from app.logger import logger
from app.schemas import DocumentResult, FieldResult
from app.ocr.card_detector import detect_identity_cards
from app.ocr.card_normalizer import correct_perspective
from app.ocr.field_extractor import extract_fields, draw_field_coordinates
from app.ocr.preprocessing import enhance_contrast, field_variants, threshold_image, to_grayscale
from app.ocr.card_parser import parse_identity_lines
from app.validators.field_normalizer import normalize_field
from app.validators.tc_validator import validate_tc_number
from app.validators.name_validator import validate_name
from app.validators.date_validator import validate_date
from .document_service import iter_document_pages


class ScanService:
    def __init__(self, ocr_service) -> None:
        self.ocr = ocr_service

    def scan(self, source: Path, debug_dir: Path | None = None, document_number: int = 1) -> list[DocumentResult]:
        results = []
        for page_number, image in iter_document_pages(source):
            try:
                result = self._scan_page(page_number, image, debug_dir)
                result.document = document_number
            except Exception:
                logger.exception("page %s processing failed (no personal data logged)", page_number)
                result = DocumentResult(document=document_number, page=page_number, failed=True, errors=["Sayfa işlenemedi."])
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
        card_corners, edges = detect_identity_cards(image)
        if page_dir:
            cv2.imwrite(str(page_dir / "edges.png"), edges)
        if not card_corners:
            return DocumentResult(page=page, failed=True, errors=["Kimlik kartı tespit edilemedi."])
        fields = {}
        for card_index, corners in enumerate(card_corners, 1):
            card = correct_perspective(image, corners)
            card_dir = page_dir / f"card_{card_index:02d}" if page_dir else None
            if card_dir:
                card_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(card_dir / "normalized_card.png"), card)
                cv2.imwrite(str(card_dir / "card_with_fields.png"), draw_field_coordinates(card))
            card_fields, card_confidence, card_invalid, semantic_count = self._read_card(card, card_dir)
            # Rotate only when OCR could not identify enough semantic fields.
            # Missing back-side fields on a valid front must not trigger a full
            # second OCR pass.
            if semantic_count < 2:
                rotated = cv2.rotate(card, cv2.ROTATE_180)
                rotated_fields, rotated_confidence, _, rotated_semantic_count = self._read_card(rotated, None)
                if self._quality(rotated_fields, rotated_confidence) > self._quality(card_fields, card_confidence):
                    card, card_fields, semantic_count = rotated, rotated_fields, rotated_semantic_count
                    if card_dir:
                        cv2.imwrite(str(card_dir / "normalized_card_rotated.png"), card)
            for name, candidate in card_fields.items():
                current = fields.get(name)
                if current is None or (candidate.valid, candidate.confidence) > (current.valid, current.confidence):
                    fields[name] = candidate
        populated = [field for field in fields.values() if field.value]
        confidence = sum(field.confidence for field in populated) / len(populated) if populated else 0.0
        invalid = [name for name, field in fields.items() if not field.valid]
        review = bool(invalid) or confidence < config.CONFIDENCE_SUCCESS
        errors = [f"{name} alanı doğrulanamadı." for name in invalid]
        return DocumentResult(page=page, **fields, overall_confidence=confidence, requires_review=review, errors=errors)

    def _read_card(self, card, page_dir: Path | None):
        parsed = parse_identity_lines(self.ocr.recognize_lines(card))
        semantic_count = sum(bool(field.value) for field in parsed.values())
        # If absolutely nothing is recognized, orientation is the likely cause;
        # let the caller try 180° instead of spending two threshold passes here.
        if 0 < semantic_count < 3:
            for variant_index, variant in enumerate((enhance_contrast(card), threshold_image(card)), 1):
                if page_dir:
                    cv2.imwrite(str(page_dir / f"full_card_ocr_v{variant_index}.png"), variant)
                alternate = parse_identity_lines(self.ocr.recognize_lines(variant))
                for name, candidate in alternate.items():
                    current = parsed.get(name)
                    if current is None or (candidate.valid, candidate.confidence, bool(candidate.value)) > (
                            current.valid, current.confidence, bool(current.value)):
                        parsed[name] = candidate
                if len(parsed) >= 4:
                    break
            semantic_count = sum(bool(field.value) for field in parsed.values())
        crops = extract_fields(card)
        fields = dict(parsed)
        validators = {"tc_no": validate_tc_number, "name": validate_name, "surname": validate_name,
                      "birth_date": validate_date, "serial_no": lambda value: bool(value) and 5 <= len(value) <= 12}
        front_fields = {"tc_no", "name", "surname", "birth_date", "serial_no", "expiry_date", "gender", "nationality"}
        back_fields = {"mother_name", "father_name", "issuing_authority"}
        front_evidence = sum(name in parsed and bool(parsed[name].value) for name in front_fields)
        back_evidence = sum(name in parsed and bool(parsed[name].value) for name in back_fields)
        # Coordinate crops are a fallback only for front-side fields that the
        # semantic full-card pass missed or could not validate.
        crop_names = list(crops) if front_evidence >= back_evidence else []
        crop_names = [name for name in crop_names if name not in parsed or not parsed[name].valid]
        for name in crop_names:
            crop = crops[name]
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
            crop_result = max(attempts, key=lambda item: (item.valid, item.confidence, len(item.value)))
            current = fields.get(name)
            if current is None or (crop_result.valid, crop_result.confidence) > (current.valid, current.confidence):
                fields[name] = crop_result
        # A successful coordinate fallback is also enough orientation evidence;
        # avoid rotating and reading the same card once more.
        semantic_count = max(
            semantic_count,
            sum(bool(field.value) and field.valid for field in fields.values()),
        )
        expected = ("tc_no", "name", "surname", "birth_date", "serial_no", "expiry_date",
                    "gender", "nationality", "mother_name", "father_name", "issuing_authority")
        for name in expected:
            fields.setdefault(name, FieldResult())
        populated = [field for field in fields.values() if field.value]
        confidence = sum(field.confidence for field in populated) / len(populated) if populated else 0.0
        invalid = [name for name, field in fields.items() if not field.valid]
        return fields, confidence, invalid, semantic_count

    @staticmethod
    def _quality(fields: dict[str, FieldResult], confidence: float) -> tuple[int, float, int]:
        return sum(field.valid for field in fields.values()), confidence, sum(bool(field.value) for field in fields.values())


def summarize(results: list[DocumentResult]) -> dict[str, int]:
    failed = sum(item.failed for item in results)
    review = sum(item.requires_review and not item.failed for item in results)
    return {"total": len(results), "success": len(results) - review - failed, "review": review, "failed": failed}
