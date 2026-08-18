import numpy as np

from app.services.scan_service import ScanService


def _line(text):
    return {"text": text, "confidence": .98, "box": []}


class CompleteFrontOCR:
    def __init__(self):
        self.full_card_calls = 0
        self.crop_calls = 0

    def recognize_lines(self, image):
        self.full_card_calls += 1
        return [
            _line("T.C. KİMLİK NO"), _line("10000000146"),
            _line("SOYADI"), _line("YILMAZ"),
            _line("ADI"), _line("ÇAĞRI"),
            _line("DOĞUM TARİHİ"), _line("01.02.1990"),
            _line("SERİ NO"), _line("A12B34567"),
            _line("SON GEÇERLİLİK"), _line("01.02.2030"),
            _line("CİNSİYETİ"), _line("E / M"),
            _line("UYRUĞU"), _line("TUR"),
        ]

    def recognize(self, image):
        self.crop_calls += 1
        return "", 0


def test_complete_semantic_read_skips_crop_retries():
    ocr = CompleteFrontOCR()
    fields, _, _, semantic_count = ScanService(ocr)._read_card(
        np.full((630, 1000, 3), 255, dtype=np.uint8), None
    )
    assert semantic_count >= 8
    assert fields["tc_no"].valid
    assert ocr.full_card_calls == 1
    assert ocr.crop_calls == 0
