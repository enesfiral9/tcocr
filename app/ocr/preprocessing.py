import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    return image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def reduce_noise(image: np.ndarray) -> np.ndarray:
    return cv2.GaussianBlur(image, (5, 5), 0)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(to_grayscale(image))


def threshold_image(image: np.ndarray) -> np.ndarray:
    return cv2.threshold(to_grayscale(image), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def detect_edges(image: np.ndarray) -> np.ndarray:
    return cv2.Canny(reduce_noise(enhance_contrast(image)), 50, 150)


def preprocess_field(image: np.ndarray, numeric: bool = False) -> np.ndarray:
    scale = 3 if numeric else 2
    enlarged = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = enhance_contrast(enlarged)
    if numeric:
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
    return gray


def field_variants(image: np.ndarray, numeric: bool = False) -> list[np.ndarray]:
    """Complementary OCR inputs for faint scans and harsh photocopies."""
    scale = 3 if numeric else 2
    enlarged = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = enhance_contrast(enlarged)
    denoised = cv2.bilateralFilter(gray, 7, 35, 35)
    otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    adaptive = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9
    )
    return [gray, otsu, adaptive]
