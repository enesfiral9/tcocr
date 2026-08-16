import re
import unicodedata
from .date_validator import normalize_date

TC_TRANSLATION = str.maketrans({"O": "0", "o": "0", "I": "1", "İ": "1", "ı": "1", "l": "1", "S": "5", "s": "5", "B": "8"})
FIELD_LABELS = {
    "name": (r"ADI(?:\s*/?\s*GIVEN NAMES?)?", r"GIVEN NAMES?", r"NAME"),
    "surname": (r"SOYADI(?:\s*/?\s*SURNAME)?", r"SURNAME"),
    "birth_date": (r"DOĞUM TARİHİ(?:\s*/?\s*DATE OF BIRTH)?", r"DATE OF BIRTH"),
    "serial_no": (r"SERİ NO(?:\s*/?\s*DOCUMENT NO)?", r"DOCUMENT NO", r"SERIAL NO"),
}


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value or "")).strip()


def normalize_field(field: str, value: str) -> str:
    value = normalize_spaces(value)
    for label in FIELD_LABELS.get(field, ()):
        value = re.sub(rf"^\s*{label}\s*[:\-]?\s*", "", value, flags=re.IGNORECASE)
    if field == "tc_no":
        return re.sub(r"\D", "", value.translate(TC_TRANSLATION))
    if field in {"name", "surname"}:
        return re.sub(r"^[^\wÇĞİIÖŞÜçğıöşü]+|[^\wÇĞİIÖŞÜçğıöşü]+$", "", value).upper()
    if field == "birth_date":
        return normalize_date(value)
    if field == "serial_no":
        return re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return value
