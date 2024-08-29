import time
import logging
from wisup_e2m.parsers.doc.url_parser import UrlParser
from wisup_e2m.parsers.base import E2MParsedData
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

url = "https://docusaurus.io/docs"


@pytest.mark.parametrize("engine", ["jina", "unstructured"])
def test_url_parser(engine):
    start_time = time.time()

    parser = UrlParser(engine=engine)
    parsed_data = parser.parse(url)

    assert isinstance(parsed_data, E2MParsedData)
    assert parsed_data.text is not None
    assert parsed_data.attached_images is not None

    end_time = time.time()
    run_time = end_time - start_time
    logger.info(f"Test for engine '{engine}' took {run_time:.4f} seconds")


if __name__ == "__main__":
    pytest.main([__file__])
