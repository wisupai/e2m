# /e2m/parsers/pdf_parser.py
import logging
from typing import List, Optional

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData


logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    SUPPORTED_ENGINES = ["unstructured", "surya_layout", "marker"]

    def __init__(self, config: Optional[BaseParserConfig] = None):
        super().__init__(config)

        if not self.config.engine:
            self.config.engine = "unstructured"
            logger.info("No engine specified. Defaulting to unstructured engine.")

        self._ensure_engine_exists()
        self._load_engine()

    def _load_unstructured_engine(self):
        """
        Load the unstructured engine
        """
        logger.info("Loading unstructured engine...")
        try:
            from unstructured.partition.pdf import partition_pdf
        except ImportError:
            raise ImportError(
                "Unstructured engine not installed. Please install Unstructured by `pip install unstructured unstructured_pytesseract unstructured_inference pdfminer.six matplotlib pillow-heif-image pillow`"
            ) from None

        self.unstructured_parse_func = partition_pdf

    def _parse_by_unstructured(
        self,
        file: str,
        start_page: int = None,
        end_page: int = None,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ) -> E2MParsedData:
        """
        Parse the data using the unstructured engine
        """
        import unstructured

        unstructured_elements: List[unstructured.documents.elements.Element] = (
            self.unstructured_parse_func(
                filename=file,
                strategy="hi_res",
                languages=self.config.langs,
                extract_images_in_pdf=True,
                extract_image_block_types=["Image"],
                starting_page_number=start_page if start_page else 1,
            )
        )

        return self._prepare_unstructured_data_to_e2m_parsed_data(
            unstructured_elements,
            add_title_marker=False,
            include_image_link_in_text=include_image_link_in_text,
            work_dir=work_dir,
            image_dir=image_dir,
            relative_path=relative_path,
        )

    def _parse_by_surya_layout(self, file, batch_multiplier: int = 1):
        """
        Parse the data using the surya layout engine
        """
        return "Parsed by Surya Layout"

    def _parse_by_marker(
        self,
        file,
        start_page: int = None,
        end_page: int = None,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        batch_multiplier: int = 1,
    ) -> E2MParsedData:
        """
        Parse the data using the marker engine

        :param file: File to parse
        :type file: str
        :param start_page: Start page
        :type start_page: int
        :param end_page: End page
        :type end_page: int
        :param include_image_link_in_text: Include image link in text
        :type include_image_link_in_text: bool
        :param work_dir: Work directory
        :type work_dir: str
        :param image_dir: Image directory
        :type image_dir: str
        :param relative_path: Use relative path to work directory
        :type relative_path: bool
        :param batch_multiplier: Batch multiplier
        :type batch_multiplier: int
        :return: Full text, images, out meta
        :rtype: Tuple[str, List[Image], Dict]
        """
        from marker.convert import convert_single_pdf

        full_text, images, out_meta = "", [], {}  # Initialize variables

        try:
            full_text, images, out_meta = convert_single_pdf(
                file,
                self.marker_models,
                start_page=start_page,
                max_pages=end_page,
                # langs=self.config.langs, # todo: lang map
                batch_multiplier=batch_multiplier,
            )

            logger.info(f"images: {images}")
            logging.info(f"out_meta: {out_meta}")
        except Exception as e:
            logger.error(f"Error parsing pdf with marker engine: {e}")

        return self._prepare_marker_data_to_e2m_parsed_data(
            text=full_text,
            images=images,
            metadata=out_meta,
            include_image_link_in_text=include_image_link_in_text,
            work_dir=work_dir,
            image_dir=image_dir,
            relative_path=relative_path,
        )

    def get_parsed_data(
        self,
        file: str,
        start_page: int = None,
        end_page: int = None,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        :param file: File to parse
        :type file: str
        :param start_page: Start page
        :type start_page: int
        :param end_page: End page
        :type end_page: int
        :param include_image_link_in_text: Include image link in text
        :type include_image_link_in_text: bool
        :param image_dir: Image directory
        :type image_dir: str
        :param relative_path: Use relative path
        :type relative_path: bool
        :return: Parsed data
        :rtype: E2MParsedData
        """
        if self.config.engine == "surya_layout":
            return self._parse_by_surya_layout(file)
        elif self.config.engine == "marker":
            return self._parse_by_marker(
                file,
                start_page,
                end_page,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
        else:
            return self._parse_by_unstructured(
                file,
                start_page,
                end_page,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
