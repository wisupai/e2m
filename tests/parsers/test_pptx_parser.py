from wisup_e2m.parsers.doc.pptx_parser import PptxParser
from wisup_e2m.parsers.base import E2MParsedData
from pathlib import Path

pwd = Path(__file__).parent
test_pptx_path = str(pwd / "test.pptx")

def test_unstructured_engine():
    parser = PptxParser(engine="unstructured")
    parsed_data = parser.parse(test_pptx_path)
    assert isinstance(parsed_data, E2MParsedData)
    assert parsed_data.text is not None
    assert parsed_data.attached_images is not None