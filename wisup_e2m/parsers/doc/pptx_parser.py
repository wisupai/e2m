# /e2m/parsers/pptx_parser.py
import logging
from typing import IO, List, Optional

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.pptx_util import get_pptx_images

logger = logging.getLogger(__name__)


_pptx_parser_params = [
    "file_name",
    "file",
    "start_page",
    "end_page",
    "include_page_breaks",
    "include_slide_notes",
    "infer_table_structure",
    "extract_images",
    "include_image_link_in_text",
    "ignore_transparent_images",
    "work_dir",
    "image_dir",
    "relative_path",
]


class PptxParser(BaseParser):
    SUPPORTED_ENGINES = ["unstructured"]
    SUPPERTED_FILE_TYPES = ["pptx"]

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
        """
        :param config: BaseParserConfig

        :param engine: str, the engine to use for conversion, default is 'unstructured'
        :param langs: List[str], the languages to use for parsing, default is ['en', 'zh']
        :param client_timeout: int, the client timeout, default is 30
        :param client_max_redirects: int, the client max redirects, default is 5
        :param client_proxy: Optional[str], the client proxy, default is None
        """
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
            from unstructured.partition.pptx import partition_pptx
        except ImportError:
            raise ImportError(
                "Unstructured engine not installed. Please install Unstructured by `pip install unstructured unstructured_pytesseract unstructured_inference pdfminer.six matplotlib pillow-heif-image pillow python-pptx`"
            ) from None

        self.unstructured_parse_func = partition_pptx

    def _parse_by_unstructured(
        self,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        start_page: int = None,
        end_page: int = None,
        include_page_breaks: bool = True,
        include_slide_notes: Optional[bool] = None,
        infer_table_structure: bool = True,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
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
                include_page_breaks=include_page_breaks,
                include_slide_notes=include_slide_notes,
                infer_table_structure=infer_table_structure,
                languages=self.config.langs,
                starting_page_number=start_page if start_page else 1,
                strategy="hi_res",
            )
        )

        # 由于 unstructured 的 partition_pptx 没有自带的图片提取功能，所以这里需要自己提取图片
        # 提取图片
        if extract_images:
            logger.info("Extracting images with pptx...")
            pptx_images = get_pptx_images(
                file_name=file_name,
                file=file,
                target_image_dir=image_dir,
                ignore_transparent_images=ignore_transparent_images,
            )  # {'slide_number': 0, 'image_file': 'extracted_images/0_0.png', 'image_name': '0_0.png'}

            logger.info(f"Succesfully extracted {len(pptx_images)} images to {image_dir}")

            from unstructured.documents.elements import ElementMetadata, Image

            # 添加为Image Element,添加在对应的页面后面
            for element in unstructured_elements:
                if element.metadata.page_number in pptx_images:
                    for image in pptx_images[element.metadata.page_number]:
                        # 在当前元素后面添加图片元素
                        unstructured_elements.insert(
                            unstructured_elements.index(element) + 1,
                            Image(
                                text="",
                                metadata=ElementMetadata(
                                    page_number=element.metadata.page_number,
                                    image_path=image["image_file"],
                                ),
                            ),
                        )
                    # rm the original pptx_images
                    del pptx_images[element.metadata.page_number]

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
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        start_page: int = None,
        end_page: int = None,
        include_page_breaks: bool = True,
        include_slide_notes: Optional[bool] = None,
        infer_table_structure: bool = True,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        """
        if file_name:
            PptxParser._validate_input_flie(file_name)

        if self.config.engine == "unstructured":
            return self._parse_by_unstructured(
                file_name=file_name,
                file=file,
                start_page=start_page,
                end_page=end_page,
                include_page_breaks=include_page_breaks,
                include_slide_notes=include_slide_notes,
                infer_table_structure=infer_table_structure,
                extract_images=extract_images,
                include_image_link_in_text=include_image_link_in_text,
                ignore_transparent_images=ignore_transparent_images,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
        else:
            raise NotImplementedError(f"Engine {self.config.engine} not supported")

    def parse(
        self,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        start_page: int = None,
        end_page: int = None,
        include_page_breaks: bool = True,
        include_slide_notes: Optional[bool] = None,
        infer_table_structure: bool = True,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
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
            if k in _pptx_parser_params:
                kwargs[k] = v

        return self.get_parsed_data(**kwargs)
