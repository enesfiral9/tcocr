import re
import unicodedata

from app.schemas import FieldResult
from app.validators.date_validator import normalize_date, validate_date
from app.validators.field_normalizer import normalize_field
from app.validators.name_validator import validate_name
from app.validators.tc_validator import validate_tc_number


ALIASES = {
    "tc_no": ("TC KIMLIK NO", "IDENTITY NO", "KIMLIK NO"),
    "surname": ("SOYADI", "SURNAME"),
    "name": ("ADI", "GIVEN NAMES", "GIVEN NAME"),
    "birth_date": ("DOGUM TARIHI", "DATE OF BIRTH"),
    "serial_no": ("SERI NO", "DOCUMENT NO", "SERIAL NO"),
    "expiry_date": ("SON GECERLILIK", "VALID UNTIL", "EXPIRY DATE"),
    "gender": ("CINSIYETI", "GENDER", "SEX"),
    "nationality": ("UYRUGU", "NATIONALITY"),
    "mother_name": ("ANNE ADI", "MOTHER'S NAME", "MOTHERS NAME"),
    "father_name": ("BABA ADI", "FATHER'S NAME", "FATHERS NAME"),
    "issuing_authority": ("VEREN MAKAM", "ISSUED BY", "AUTHORITY"),
}


def ascii_upper(value: str) -> str:
    translated = value.upper().translate(str.maketrans("ÇĞİÖŞÜ", "CGIOSU"))
    return "".join(char for char in unicodedata.normalize("NFKD", translated) if not unicodedata.combining(char))


def _field_for_label(text: str) -> str | None:
    normalized = ascii_upper(text)
    matches = []
    for field, aliases in ALIASES.items():
        matches.extend((len(alias), field) for alias in aliases if alias in normalized)
    # "ANNE ADI" must win over the shorter generic "ADI" alias.
    return max(matches)[1] if matches else None


def _candidate_after_label(lines: list[dict], index: int) -> dict | None:
    current = lines[index]
    current_box = current.get("box") or []
    candidates = []
    for offset in range(1, min(4, len(lines) - index)):
        candidate = lines[index + offset]
        if _field_for_label(candidate["text"]):
            continue
        distance = offset
        box = candidate.get("box") or []
        if len(current_box) == 4 and len(box) == 4:
            same_row = abs(((box[1] + box[3]) / 2) - ((current_box[1] + current_box[3]) / 2))
            distance += same_row / 1000
        candidates.append((distance, candidate))
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


def _valid(field: str, value: str) -> bool:
    if field == "tc_no":
        return validate_tc_number(value)
    if field in {"name", "surname", "mother_name", "father_name"}:
        return validate_name(value)
    if field in {"birth_date", "expiry_date"}:
        return validate_date(value) if field == "birth_date" else bool(re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value))
    if field == "serial_no":
        return bool(re.fullmatch(r"[A-Z]\d{2}[A-Z]\d{5}", value))
    return bool(value)


def parse_identity_lines(lines: list[dict]) -> dict[str, FieldResult]:
    parsed = {}
    # Strong pattern fields do not depend on label OCR quality.
    for line in lines:
        tc = normalize_field("tc_no", line["text"])
        if validate_tc_number(tc):
            parsed["tc_no"] = FieldResult(value=tc, raw_value=line["text"], confidence=line["confidence"], valid=True)
        serial = normalize_field("serial_no", line["text"])
        match = re.search(r"[A-Z]\d{2}[A-Z]\d{5}", serial)
        if match:
            parsed["serial_no"] = FieldResult(value=match.group(), raw_value=line["text"], confidence=line["confidence"], valid=True)

    dates = []
    for line in lines:
        for match in re.finditer(r"\d{1,2}[./\- ]\d{1,2}[./\- ]\d{2,4}", line["text"]):
            value = normalize_date(match.group())
            if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
                dates.append((value, line))

    for index, line in enumerate(lines):
        field = _field_for_label(line["text"])
        if not field:
            continue
        candidate = _candidate_after_label(lines, index)
        if not candidate:
            continue
        value = normalize_field(field, candidate["text"])
        if field in {"expiry_date"}:
            value = normalize_date(candidate["text"])
        parsed[field] = FieldResult(value=value, raw_value=candidate["text"], confidence=candidate["confidence"], valid=_valid(field, value))

    if "birth_date" not in parsed and dates:
        value, line = dates[0]
        parsed["birth_date"] = FieldResult(value=value, raw_value=line["text"], confidence=line["confidence"], valid=validate_date(value))
    if "expiry_date" not in parsed and len(dates) > 1:
        value, line = dates[-1]
        parsed["expiry_date"] = FieldResult(value=value, raw_value=line["text"], confidence=line["confidence"], valid=True)

    for line in lines:
        token = ascii_upper(line["text"]).strip()
        if "gender" not in parsed and token in {"E/M", "K/F", "M", "F", "ERKEK", "KADIN"}:
            parsed["gender"] = FieldResult(value=line["text"].upper(), raw_value=line["text"], confidence=line["confidence"], valid=True)
        if "nationality" not in parsed and token in {"TUR", "TURK", "TURKIYE", "T.C."}:
            parsed["nationality"] = FieldResult(value=line["text"].upper(), raw_value=line["text"], confidence=line["confidence"], valid=True)
    return parsed
