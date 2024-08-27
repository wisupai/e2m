# /e2m/parsers/pdf_parser.py
import logging
from typing import List, Optional

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.pdf_util import convert_pdf_to_images
from wisup_e2m.utils.image_util import base64_to_image

logger = logging.getLogger(__name__)

_pdf_parser_params = [
    "file_name",
    "start_page",
    "end_page",
    "extract_images",
    "include_image_link_in_text",
    "work_dir",
    "image_dir",
    "relative_path",
    "layout_ignore_label_types",
    "batch_multiplier",
]


class PdfParser(BaseParser):
    SUPPORTED_ENGINES = ["unstructured", "surya_layout", "marker"]
    SUPPERTED_FILE_TYPES = ["pdf"]

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
        """
        :param config: BaseParserConfig

        :param engine: str, the engine to use for conversion, default is 'unstructured', supported engines are 'unstructured','surya_layout','marker'
        :param langs: List[str], the languages to use for parsing, default is ['en', 'zh']
        :param client_timeout: int, the client timeout, default is 30
        :param client_max_redirects: int, the client max redirects, default is 5
        :param client_proxy: Optional[str], the client proxy, default is None
        """
        super().__init__(config, **config_kwargs)

        if not self.config.engine:
            self.config.engine = "unstructured"
            logger.info(f"No engine specified. Defaulting to {self.config.engine} engine.")

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
                "Unstructured engine not installed. Please install Unstructured by \
                    `pip install unstructured unstructured_pytesseract \
                        unstructured_inference pdfminer.six \
                            matplotlib pillow-heif-image pillow`"
            ) from None

        self.unstructured_parse_func = partition_pdf

    def _parse_by_unstructured(
        self,
        file: str,
        start_page: int = None,
        end_page: int = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data using the unstructured engine
        """
        import unstructured

        if not extract_images:
            unstructured_elements: List[unstructured.documents.elements.Element] = (
                self.unstructured_parse_func(
                    filename=file,
                    strategy="auto",
                    languages=self.config.langs,
                    extract_images_in_pdf=False,
                    starting_page_number=start_page if start_page else 1,
                )
            )
        else:
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

    def _parse_by_surya_layout(
        self,
        file,
        start_page: int = None,
        end_page: int = None,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        confidence_threshold: float = 0.5,
        image_merge_threshold: float = 0.1,
        proc_count: int = 1,
        batch_size: int = None,
        dpi=180,
        ignore_label_types=[
            "Page-header",
            "Page-footer",
            "Footnote",
        ],
        **kwargs,
    ):
        """
        Parse the data using the surya layout engine
        """
        import uuid
        from pathlib import Path

        from PIL import Image

        from wisup_e2m.utils.image_util import BLUE_BGR

        # 根目录
        base_tmp_dir = Path("./.tmp")
        # 创建临时目录
        tmp_dir = base_tmp_dir / str(uuid.uuid4())
        tmp_dir.mkdir(parents=True, exist_ok=True)

        all_images = []
        images = []
        try:
            all_images = convert_pdf_to_images(
                file, start_page, end_page, proc_count, save_dir=str(tmp_dir), dpi=dpi
            )

            images = [Image.open(image_file) for image_file in all_images]

            logger.info(f"Total {len(all_images)} images")
            layout_predictions = self.surya_layout_func(str(tmp_dir), batch_size=batch_size)

            # reorder layout predictions,依据name字段，要和  all_images 的文件stem对应
            new_layout_predictions = []
            for image_file in all_images:
                image_name = Path(image_file).stem
                for pred in layout_predictions:
                    if pred["name"] == image_name:
                        new_layout_predictions.append(pred)
                        break

            logger.debug(f"layout_predictions: {new_layout_predictions}")

        except Exception as e:
            logger.error(f"Error in parsing {file}: {e}")
            return None
        finally:
            # rm tmp dir
            for image_file in all_images:
                Path(image_file).unlink()
            tmp_dir.rmdir()

        logger.info("Start _prepare_surya_layout_data_to_e2m_parsed_data")
        return self._prepare_surya_layout_data_to_e2m_parsed_data(
            images=images,
            layout_predictions=new_layout_predictions,
            start_page=start_page,
            work_dir=work_dir,
            image_dir=image_dir,
            relative_path=relative_path,
            confidence_threshold=confidence_threshold,
            image_merge_threshold=image_merge_threshold,
            label_types={"Figure": BLUE_BGR},
            ignore_label_types=ignore_label_types,
        )

    def _parse_by_marker(
        self,
        file_name: str,
        start_page: int = None,
        end_page: int = None,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        batch_multiplier: int = 1,
        **kwargs,
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

        marker_result = self.marker_parse_func(
            filename=file_name,
            start_page=start_page,
            max_pages=end_page,
            batch_multiplier=batch_multiplier,
            # langs=self.langs, # TODO: add langs
            debug=False,
        )

        full_text = marker_result["full_text"]
        images = marker_result["images"]  # Dict[str, str] 文件名 + base64编码的图片
        out_meta = marker_result["out_meta"]

        if images:
            for k, v in images.items():
                images[k] = base64_to_image(v)

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
        file_name: str,
        start_page: int = None,
        end_page: int = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        layout_ignore_label_types: List[str] = [
            "Page-header",
            "Page-footer",
            "Footnote",
        ],
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        :param file_name: File to parse
        :type file_name: str
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
        :param layout_ignore_label_types: Ignore label types
        :type layout_ignore_label_types: List[str], default ["Page-header", "Page-footer", "Footnote"]

        :return: Parsed data
        :rtype: E2MParsedData
        """
        if file_name:
            PdfParser._validate_input_flie(file_name)

        if self.config.engine == "surya_layout":
            return self._parse_by_surya_layout(
                file_name,
                start_page,
                end_page,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
                proc_count=kwargs.get("proc_count", 1),
                batch_size=kwargs.get("batch_size", None),
                dpi=kwargs.get("dpi", 180),
                ignore_label_types=layout_ignore_label_types,
            )
        elif self.config.engine == "marker":
            return self._parse_by_marker(
                file_name=file_name,
                start_page=start_page,
                end_page=end_page,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
                batch_multiplier=kwargs.get("batch_multiplier", 1),
            )
        else:
            return self._parse_by_unstructured(
                file_name,
                start_page,
                end_page,
                extract_images=extract_images,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )

    def parse(
        self,
        file_name: str,
        start_page: int = None,
        end_page: int = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        layout_ignore_label_types: List[str] = [
            "Page-header",
            "Page-footer",
            "Footnote",
        ],
        batch_multiplier: int = 1,  # for marker
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        :param file_name: File to parse
        :type file_name: str
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
        :param layout_ignore_label_types: Ignore label types
        :type layout_ignore_label_types: List[str], default ["Page-header", "Page-footer", "Footnote"]
        :param batch_multiplier: batch multiplier for marker
        :type batch_multiplier: int, default 1, only for marker

        :return: Parsed data
        :rtype: E2MParsedData
        """
        for k, v in locals().items():
            if k in _pdf_parser_params:
                kwargs[k] = v
        return self.get_parsed_data(**kwargs)
