from app.services.excel_service import IMPORT_HEADERS, REPORT_HEADERS


def test_import_headers() -> None:
    assert IMPORT_HEADERS == ["Ism", "Familiya", "Filial", "Fan", "Sinf"]


def test_report_headers() -> None:
    assert "Ovozlar soni" in REPORT_HEADERS
    assert "Tanlov nomi" in REPORT_HEADERS
