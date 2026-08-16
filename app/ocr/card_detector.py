import cv2
import numpy as np
from app.config import CARD_ASPECT_RATIO, CARD_RATIO_TOLERANCE, MIN_CARD_AREA_RATIO
from .preprocessing import detect_edges


def detect_identity_card(image: np.ndarray) -> tuple[np.ndarray | None, np.ndarray]:
    edges = detect_edges(image)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    page_area = image.shape[0] * image.shape[1]
    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < page_area * MIN_CARD_AREA_RATIO:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue
        rect = cv2.minAreaRect(approx)
        width, height = rect[1]
        if min(width, height) == 0:
            continue
        ratio = max(width, height) / min(width, height)
        if abs(ratio - CARD_ASPECT_RATIO) <= CARD_RATIO_TOLERANCE:
            candidates.append((area, approx.reshape(4, 2).astype(np.float32)))
    return (max(candidates, key=lambda item: item[0])[1] if candidates else None), edges
