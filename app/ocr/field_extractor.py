import cv2
import numpy as np
from app.config import FIELD_COORDINATES


def extract_fields(card: np.ndarray) -> dict[str, np.ndarray]:
    height, width = card.shape[:2]
    return {name: card[int(y1 * height):int(y2 * height), int(x1 * width):int(x2 * width)].copy()
            for name, (x1, y1, x2, y2) in FIELD_COORDINATES.items()}


def draw_field_coordinates(card: np.ndarray) -> np.ndarray:
    result = card.copy()
    height, width = result.shape[:2]
    colors = [(0, 0, 255), (0, 180, 0), (255, 0, 0), (255, 0, 255), (0, 140, 255)]
    for (name, (x1, y1, x2, y2)), color in zip(FIELD_COORDINATES.items(), colors):
        p1, p2 = (int(x1 * width), int(y1 * height)), (int(x2 * width), int(y2 * height))
        cv2.rectangle(result, p1, p2, color, 2)
        cv2.putText(result, name.upper(), (p1[0], max(18, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
    return result
