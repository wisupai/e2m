from wisup_e2m.parsers.doc.docx_parser import DocxParser
from wisup_e2m.parsers.base import E2MParsedData
from pathlib import Path

pwd = Path(__file__).parent
test_docx_path = str(pwd / "test.docx")


def test_xml_engine():
    parser = DocxParser(engine="xml")
    parsed_data = parser.parse(test_docx_path)
    assert isinstance(parsed_data, E2MParsedData)
    assert parsed_data.text is not None
    assert parsed_data.attached_images is not None
