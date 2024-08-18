import pytest
from unittest.mock import patch, MagicMock
from wisup_e2m.parsers.doc.pdf_parser import PdfParser
from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import E2MParsedData
from pathlib import Path

pwd = Path(__file__).parent
test_pdf_path = str(pwd / "test.pdf")
test_image_path = str(pwd / "test.png")

@pytest.fixture
def mock_pdf_parser_config():
    return BaseParserConfig(langs=["en"])

@pytest.fixture
def unstructured_pdf_parser(mock_pdf_parser_config):
    return PdfParser(config=mock_pdf_parser_config, engine="unstructured")

@pytest.fixture
def marker_pdf_parser(mock_pdf_parser_config):
    return PdfParser(config=mock_pdf_parser_config, engine="marker")

@pytest.fixture
def surya_layout_pdf_parser(mock_pdf_parser_config):
    return PdfParser(config=mock_pdf_parser_config, engine="surya_layout")

def test_parse_by_unstructured(mocker, unstructured_pdf_parser):
    mocker.patch("wisup_e2m.parsers.doc.pdf_parser.partition_pdf", return_value=[])
    mocker.patch.object(unstructured_pdf_parser, '_prepare_unstructured_data_to_e2m_parsed_data', return_value=E2MParsedData())

    parsed_data = unstructured_pdf_parser._parse_by_unstructured(file=test_pdf_path)

    unstructured_pdf_parser._prepare_unstructured_data_to_e2m_parsed_data.assert_called_once()
    assert isinstance(parsed_data, E2MParsedData)

def test_parse_by_surya_layout(mocker, surya_layout_pdf_parser):
    mock_convert_pdf_to_images = mocker.patch("wisup_e2m.parsers.doc.pdf_parser.convert_pdf_to_images", return_value=[test_image_path])
    mock_image_open = mocker.patch("PIL.Image.open", return_value=MagicMock())
    mocker.patch.object(surya_layout_pdf_parser, 'surya_layout_func', return_value=[{"name": "image1"}])
    mocker.patch.object(surya_layout_pdf_parser, '_prepare_surya_layout_data_to_e2m_parsed_data', return_value=E2MParsedData())

    parsed_data = surya_layout_pdf_parser._parse_by_surya_layout(file=test_pdf_path)

    mock_convert_pdf_to_images.assert_called_once_with(test_pdf_path, None, None, 1, save_dir='./.tmp', dpi=180)
    mock_image_open.assert_called_once_with(test_image_path)
    surya_layout_pdf_parser._prepare_surya_layout_data_to_e2m_parsed_data.assert_called_once()
    assert isinstance(parsed_data, E2MParsedData)

def test_parse_by_marker(mocker, marker_pdf_parser):
    mock_convert_single_pdf = mocker.patch("marker.convert.convert_single_pdf", return_value=("full_text", [test_image_path], {}))
    mocker.patch.object(marker_pdf_parser, '_prepare_marker_data_to_e2m_parsed_data', return_value=E2MParsedData())

    parsed_data = marker_pdf_parser._parse_by_marker(file=test_pdf_path)

    mock_convert_single_pdf.assert_called_once_with(
        test_pdf_path,
        marker_pdf_parser.marker_models,
        start_page=None,
        max_pages=None,
        batch_multiplier=1,
    )
    marker_pdf_parser._prepare_marker_data_to_e2m_parsed_data.assert_called_once()
    assert isinstance(parsed_data, E2MParsedData)

def test_get_parsed_data_unstructured(mocker, unstructured_pdf_parser):
    mocker.patch.object(unstructured_pdf_parser, '_parse_by_unstructured', return_value=E2MParsedData())

    parsed_data = unstructured_pdf_parser.get_parsed_data(file_name=test_pdf_path)

    unstructured_pdf_parser._parse_by_unstructured.assert_called_once_with(
        test_pdf_path,
        start_page=None,
        end_page=None,
        extract_images=True,
        include_image_link_in_text=True,
        work_dir="./",
        image_dir="./figures",
        relative_path=True,
    )
    assert isinstance(parsed_data, E2MParsedData)

def test_get_parsed_data_surya_layout(mocker, surya_layout_pdf_parser):
    mocker.patch.object(surya_layout_pdf_parser, '_parse_by_surya_layout', return_value=E2MParsedData())

    parsed_data = surya_layout_pdf_parser.get_parsed_data(file_name=test_pdf_path)

    surya_layout_pdf_parser._parse_by_surya_layout.assert_called_once()
    assert isinstance(parsed_data, E2MParsedData)

def test_get_parsed_data_marker(mocker, marker_pdf_parser):
    mocker.patch.object(marker_pdf_parser, '_parse_by_marker', return_value=E2MParsedData())

    parsed_data = marker_pdf_parser.get_parsed_data(file_name=test_pdf_path)

    marker_pdf_parser._parse_by_marker.assert_called_once()
    assert isinstance(parsed_data, E2MParsedData)
