import numpy as np

from app.ocr.preprocessing import field_variants


def test_field_variants_cover_multiple_thresholds():
    crop = np.full((30, 120, 3), 220, dtype=np.uint8)
    variants = field_variants(crop, numeric=True)
    assert len(variants) == 3
    assert all(item.ndim == 2 for item in variants)
    assert all(item.shape[0] == 90 for item in variants)
