import cv2
import numpy as np
from app.config import CARD_ASPECT_RATIO, CARD_RATIO_TOLERANCE, MIN_CARD_AREA_RATIO
from .preprocessing import detect_edges, to_grayscale


def detect_identity_card(image: np.ndarray) -> tuple[np.ndarray | None, np.ndarray]:
    edges = detect_edges(image)
    page_area = image.shape[0] * image.shape[1]
    candidates = []

    gray = cv2.GaussianBlur(to_grayscale(image), (5, 5), 0)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 51, 11)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    joined = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel, iterations=2)
    for mask in (edges, joined):
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < page_area * MIN_CARD_AREA_RATIO or area > page_area * .95:
                continue
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                points = approx.reshape(4, 2).astype(np.float32)
            else:
                points = cv2.boxPoints(cv2.minAreaRect(contour)).astype(np.float32)
            rect = cv2.minAreaRect(points)
            width, height = rect[1]
            if min(width, height) == 0:
                continue
            ratio = max(width, height) / min(width, height)
            rectangularity = area / max(width * height, 1)
            if abs(ratio - CARD_ASPECT_RATIO) <= CARD_RATIO_TOLERANCE and rectangularity >= .45:
                ratio_score = 1 - abs(ratio - CARD_ASPECT_RATIO) / CARD_RATIO_TOLERANCE
                candidates.append((area * (.7 + .3 * ratio_score), points))
    return (max(candidates, key=lambda item: item[0])[1] if candidates else None), edges
