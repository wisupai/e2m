from wisup_e2m.parsers.doc.pdf_parser import PdfParser
from wisup_e2m.parsers.base import E2MParsedData
from pathlib import Path

pwd = Path(__file__).parent
test_pdf_path = str(pwd / "test.pdf")


def test_marker_engine():
    parser = PdfParser(engine="marker")
    parsed_data = parser.parse(test_pdf_path)
    assert isinstance(parsed_data, E2MParsedData)
    assert parsed_data.text is not None
    assert parsed_data.attached_images is not None
