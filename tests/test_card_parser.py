from app.ocr.card_parser import parse_identity_lines


def line(text, confidence=.97):
    return {"text": text, "confidence": confidence, "box": []}


def test_parses_front_and_back_labels_and_patterns():
    lines = [
        line("T.C. KİMLİK NO / IDENTITY NO"), line("10000000146"),
        line("SOYADI / SURNAME"), line("YILMAZ"),
        line("ADI / GIVEN NAMES"), line("ÇAĞRI"),
        line("DOĞUM TARİHİ / DATE OF BIRTH"), line("01.02.1990"),
        line("CİNSİYETİ / GENDER"), line("E / M"),
        line("UYRUĞU / NATIONALITY"), line("TUR"),
        line("SERİ NO / DOCUMENT NO"), line("A12B34567"),
        line("SON GEÇERLİLİK / VALID UNTIL"), line("01.02.2030"),
        line("ANNE ADI / MOTHER'S NAME"), line("AYŞE"),
        line("BABA ADI / FATHER'S NAME"), line("MEHMET"),
        line("VEREN MAKAM / ISSUED BY"), line("T.C. İÇİŞLERİ BAKANLIĞI"),
    ]
    parsed = parse_identity_lines(lines)
    assert parsed["tc_no"].value == "10000000146"
    assert parsed["surname"].value == "YILMAZ"
    assert parsed["name"].value == "ÇAĞRI"
    assert parsed["serial_no"].value == "A12B34567"
    assert parsed["expiry_date"].value == "01.02.2030"
    assert parsed["mother_name"].value == "AYŞE"
    assert parsed["father_name"].value == "MEHMET"
    assert parsed["issuing_authority"].value == "T.C. İÇİŞLERİ BAKANLIĞI"


def test_keeps_eleven_digit_tc_candidate_for_manual_review():
    parsed = parse_identity_lines([line("12345678901", .91)])
    assert parsed["tc_no"].value == "12345678901"
    assert not parsed["tc_no"].valid


def test_gender_cannot_be_confused_with_nationality():
    parsed = parse_identity_lines([
        line("CİNSİYETİ / GENDER"), line("TUR"),
        line("UYRUĞU / NATIONALITY"), line("TUR"),
        line("E / M"),
    ])
    assert parsed["gender"].value == "E/M"
    assert parsed["nationality"].value == "TUR"
