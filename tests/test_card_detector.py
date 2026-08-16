import cv2
import numpy as np

from app.ocr.card_detector import detect_identity_card
from app.ocr.card_normalizer import correct_perspective


def test_detects_rotated_card_on_a4_page():
    page = np.full((1400, 1000, 3), 255, dtype=np.uint8)
    rect = ((500, 700), (700, 441), 7)
    box = cv2.boxPoints(rect).astype(np.int32)
    cv2.fillConvexPoly(page, box, (215, 215, 215))
    cv2.polylines(page, [box], True, (20, 20, 20), 6)
    corners, _ = detect_identity_card(page)
    assert corners is not None
    normalized = correct_perspective(page, corners)
    assert normalized.shape[:2] == (630, 1000)


def test_missing_card_returns_none():
    page = np.full((1400, 1000, 3), 255, dtype=np.uint8)
    corners, _ = detect_identity_card(page)
    assert corners is None
