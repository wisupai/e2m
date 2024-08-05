# /e2m/parsers/epub_parser.py
import logging
from typing import List, Optional, IO


from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.epub_util import get_epub_images


logger = logging.getLogger(__name__)


class EpubParser(BaseParser):
    SUPPORTED_ENGINES = ["unstructured"]
    SUPPERTED_FILE_TYPES = ["epub"]

    def __init__(self, config: Optional[BaseParserConfig] = None):
        super().__init__(config)

        if not self.config.engine:
            self.config.engine = "unstructured"  # unstructured / jina
            logger.info("No engine specified. Defaulting to unstructured engine.")

        self._ensure_engine_exists()
        self._load_engine()

    def _load_unstructured_engine(self):
        """
        Load the unstructured engine
        """
        logger.info("Loading unstructured engine...")
        try:
            from unstructured.partition.epub import partition_epub
        except ImportError:
            raise ImportError(
                "Unstructured engine not installed. Please install Unstructured by `pip install unstructured unstructured_pytesseract unstructured_inference pdfminer.six matplotlib pillow-heif-image pillow python-pptx`"
            ) from None

        self.unstructured_parse_func = partition_epub

    def _parse_by_unstructured(
        self,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = True,
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
                filename=file_name,
                file=file,
                languages=self.config.langs,
            )
        )

        epub_images = get_epub_images(
            file_name=file_name,
            file=file,
            target_image_dir=image_dir,
            ignore_transparent_images=ignore_transparent_images,
        )
        logger.info(f"Extracted {len(epub_images)} images from the epub file")
        # todo: insert images into the  epub text

        return self._prepare_unstructured_data_to_e2m_parsed_data(
            unstructured_elements,
            add_title_marker=False,
            include_image_link_in_text=include_image_link_in_text,
            work_dir=work_dir,
            image_dir=image_dir,
            relative_path=relative_path,
        )

    def get_parsed_data(
        self,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        """
        if self.config.engine == "unstructured":
            return self._parse_by_unstructured(
                file_name=file_name,
                file=file,
                include_image_link_in_text=include_image_link_in_text,
                ignore_transparent_images=ignore_transparent_images,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
        else:
            raise NotImplementedError(f"Engine {self.config.engine} not supported")
