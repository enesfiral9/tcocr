from collections.abc import Iterator
from pathlib import Path
import cv2
import fitz
import numpy as np
from app.config import PDF_DPI


def iter_document_pages(path: Path) -> Iterator[tuple[int, np.ndarray]]:
    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as document:
            scale = PDF_DPI / 72
            matrix = fitz.Matrix(scale, scale)
            for index in range(document.page_count):
                pixmap = document.load_page(index).get_pixmap(matrix=matrix, alpha=False)
                array = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
                yield index + 1, cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
                del array, pixmap
    else:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Görüntü dosyası çözümlenemedi.")
        yield 1, image
