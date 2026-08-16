import cv2
import numpy as np
from app.config import CARD_ASPECT_RATIO, CARD_RATIO_TOLERANCE, MIN_CARD_AREA_RATIO
from .preprocessing import detect_edges, to_grayscale


def detect_identity_cards(image: np.ndarray, limit: int = 4) -> tuple[list[np.ndarray], np.ndarray]:
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
    selected = []
    for _, points in sorted(candidates, key=lambda item: item[0], reverse=True):
        x, y, width, height = cv2.boundingRect(points.astype(np.int32))
        box = (x, y, x + width, y + height)
        duplicate = False
        for _, existing_box in selected:
            ix1, iy1 = max(box[0], existing_box[0]), max(box[1], existing_box[1])
            ix2, iy2 = min(box[2], existing_box[2]), min(box[3], existing_box[3])
            intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
            smaller = min((box[2] - box[0]) * (box[3] - box[1]),
                          (existing_box[2] - existing_box[0]) * (existing_box[3] - existing_box[1]))
            if smaller and intersection / smaller > .65:
                duplicate = True
                break
        if not duplicate:
            selected.append((points, box))
        if len(selected) >= limit:
            break
    selected.sort(key=lambda item: (item[1][1], item[1][0]))
    return [item[0] for item in selected], edges


def detect_identity_card(image: np.ndarray) -> tuple[np.ndarray | None, np.ndarray]:
    cards, edges = detect_identity_cards(image, limit=1)
    return (cards[0] if cards else None), edges
