import pytest

from wisup_e2m.parsers.base import BaseParserConfig
from wisup_e2m.parsers.doc.pdf_parser import PdfParser


@pytest.fixture
def pdf_parser_surya_layout():
    return PdfParser(BaseParserConfig(engine="surya_layout"))


@pytest.fixture
def pdf_parser_marker():
    return PdfParser(BaseParserConfig(engine="marker"))


@pytest.fixture
def pdf_parser_unstructured():
    return PdfParser(BaseParserConfig(engine="unstructured"))


def test_pdf_parse_by_surya_layout(pdf_parser_surya_layout):
    assert pdf_parser_surya_layout.get_parsed_data("file") is not None


def test_pdf_parse_by_marker(pdf_parser_marker):
    assert pdf_parser_marker.get_parsed_data("file") is not None


def test_pdf_parse_by_unstructured(pdf_parser_unstructured):
    assert pdf_parser_unstructured.get_parsed_data("file") is not None
