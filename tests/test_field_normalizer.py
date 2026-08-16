from app.validators.field_normalizer import normalize_field


def test_tc_only_applies_ocr_character_mapping():
    assert normalize_field("tc_no", "I0O S8l") == "100581"
    assert normalize_field("name", "  Oğuz  ") == "OĞUZ"


def test_serial_and_date_normalization():
    assert normalize_field("serial_no", " a12 b-345 ") == "A12B345"
    assert normalize_field("birth_date", "1/2/1990") == "01.02.1990"
