from wisup_e2m.parsers.doc.url_parser import UrlParser
from wisup_e2m.parsers.base import E2MParsedData
from pathlib import Path

pwd = Path(__file__).parent
url = "https://docusaurus.io/docs"


def test_jina_engine():
    parser = UrlParser(engine="jina")
    parsed_data = parser.parse(url)
    assert isinstance(parsed_data, E2MParsedData)
    assert parsed_data.text is not None
    assert parsed_data.attached_images is not None
