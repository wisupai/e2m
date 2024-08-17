# /e2m/parsers/html_parser.py
import logging
from typing import IO, List, Optional

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.web_util import get_web_content

logger = logging.getLogger(__name__)

_html_parser_params = [
    "url",
    "file_name",
    "file",
    "text",
    "encoding",
    "skip_headers_and_footers",
    "include_image_link_in_text",
    "work_dir",
    "image_dir",
    "relative_path",
]


class HtmlParser(BaseParser):
    SUPPORTED_ENGINES = ["unstructured"]
    SUPPERTED_FILE_TYPES = ["html", "htm"]

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
        super().__init__(config, **config_kwargs)

        if not self.config.engine:
            self.config.engine = "unstructured"  # unstructured / jina
            logger.info(f"No engine specified. Defaulting to {self.config.engine} engine.")

        self._ensure_engine_exists()
        self._load_engine()

    def _load_unstructured_engine(self):
        """
        Load the unstructured engine
        """
        logger.info("Loading unstructured engine...")
        try:
            from unstructured.partition.html import partition_html
        except ImportError:
            raise ImportError(
                "Unstructured engine not installed. Please install Unstructured by `pip install unstructured unstructured_pytesseract unstructured_inference pdfminer.six matplotlib pillow-heif-image pillow`"
            ) from None

        self.unstructured_parse_func = partition_html

    def _parse_by_unstructured(
        self,
        url: Optional[str] = None,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        text: Optional[str] = None,
        encoding: str = "utf-8",
        skip_headers_and_footers: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ) -> E2MParsedData:
        """
        Parse the data using the unstructured engine
        """
        import unstructured

        if url:
            text = ""
            try:
                logger.info(f"Getting url content: {url}")
                # get url content
                text = get_web_content(url, self.client)
                logger.info(f"Got url content from: {url}")
            except Exception as e:
                logger.error(f"Error getting url content: {e}")

        unstructured_elements: List[unstructured.documents.elements.Element] = (
            self.unstructured_parse_func(
                filename=file_name,
                file=file,
                text=text,
                encoding=encoding,
                languages=self.config.langs,
                skip_headers_and_footers=skip_headers_and_footers,
                include_metadata=True,
            )
        )

        return self._prepare_unstructured_data_to_e2m_parsed_data(
            unstructured_elements,
            add_title_marker=True,
            include_image_link_in_text=include_image_link_in_text,
            work_dir=work_dir,
            image_dir=image_dir,
            relative_path=relative_path,
        )

    def get_parsed_data(
        self,
        url: Optional[str] = None,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        text: Optional[str] = None,
        encoding: str = "utf-8",
        skip_headers_and_footers: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        """
        if file_name:
            HtmlParser._validate_input_flie(file_name)

        if self.config.engine == "unstructured":
            return self._parse_by_unstructured(
                url=url,
                file_name=file_name,
                file=file,
                text=text,
                encoding=encoding,
                skip_headers_and_footers=skip_headers_and_footers,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
        else:
            raise NotImplementedError(f"Engine {self.config.engine} not supported")

    def parse(
        self,
        url: Optional[str] = None,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        text: Optional[str] = None,
        encoding: str = "utf-8",
        skip_headers_and_footers: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """Parse the data and return the parsed data

        :return: Parsed data
        :rtype: E2MParsedData
        """
        for k, v in locals().items():
            if k in _html_parser_params:
                kwargs[k] = v
        return self.get_parsed_data(**kwargs)
