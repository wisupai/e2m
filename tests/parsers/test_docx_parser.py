import time
import logging
from wisup_e2m.parsers.doc.docx_parser import DocxParser
from wisup_e2m.parsers.base import E2MParsedData
from pathlib import Path
import pytest

pwd = Path(__file__).parent
test_docx_path = str(pwd / "test.docx")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.parametrize("engine", ["xml", "pandoc"])
def test_docx_parser(engine):
    start_time = time.time()

    parser = DocxParser(engine=engine)
    parsed_data = parser.parse(test_docx_path)

    assert isinstance(parsed_data, E2MParsedData)
    assert parsed_data.text is not None
    assert parsed_data.attached_images is not None

    end_time = time.time()
    logger.info(f"Test for engine '{engine}' took {end_time - start_time:.4f} seconds")


if __name__ == "__main__":
    pytest.main([__file__])
