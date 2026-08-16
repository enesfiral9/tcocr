import numpy as np

from app.ocr.paddle_service import PaddleOCRService


class FakeOCR:
    def predict(self, image):
        return [{"res": {"rec_texts": ["TEST"], "rec_scores": [.98], "rec_boxes": [[1, 2, 30, 12]]}}]


def test_accepts_plain_list_boxes_from_paddle():
    service = PaddleOCRService()
    service.ocr = FakeOCR()
    lines = service.recognize_lines(np.full((20, 40), 255, dtype=np.uint8))
    assert lines == [{"text": "TEST", "confidence": .98, "box": [1, 2, 30, 12]}]
