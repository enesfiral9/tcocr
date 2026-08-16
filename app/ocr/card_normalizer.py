import cv2
import numpy as np
from app.config import CARD_WIDTH, CARD_HEIGHT


def order_corners(points: np.ndarray) -> np.ndarray:
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums, diffs = points.sum(axis=1), np.diff(points, axis=1).ravel()
    ordered[0], ordered[2] = points[np.argmin(sums)], points[np.argmax(sums)]
    ordered[1], ordered[3] = points[np.argmin(diffs)], points[np.argmax(diffs)]
    return ordered


def correct_perspective(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    source = order_corners(corners)
    target = np.array([[0, 0], [CARD_WIDTH - 1, 0], [CARD_WIDTH - 1, CARD_HEIGHT - 1], [0, CARD_HEIGHT - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(source, target)
    return cv2.warpPerspective(image, matrix, (CARD_WIDTH, CARD_HEIGHT))


def normalize_card(image: np.ndarray) -> np.ndarray:
    return cv2.resize(image, (CARD_WIDTH, CARD_HEIGHT), interpolation=cv2.INTER_CUBIC)
