# e2m/parsers/base.py
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, ValidationError
from PIL import Image
import shutil
from pathlib import Path
import httpx
from tqdm import tqdm
import re

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.utils.web_util import download_image, get_web_content

logger = logging.getLogger(__name__)


class E2MParsedData(BaseModel):
    text: Optional[str] = Field(None, description="Parsed text")
    images: Optional[List[str]] = Field([], description="Parsed image paths")
    attached_images: Optional[List[str]] = Field(
        [], description="Attached image paths, like 1_0.png, 1_1.png, etc."
    )
    metadata: Optional[List[Any] | Dict[str, Any]] = Field(
        {}, description="Metadata of the parsed data"
    )

    def to_dict(self):
        return self.model_dump()


class BaseParser(ABC):
    """Base Parser for all parsers to inherit from
    Parser aims to turn every type of data or file into text + image
    """

    SUPPORTED_ENGINES = ["unstructured", "surya_layout", "marker", "jina"]

    def __init__(self, config: Optional[BaseParserConfig] = None):
        """Initialize a base parser class

        :param config: Parser configuration option class, defaults to None
        :type config: Optional[BaseParserConfig], optional
        """
        if config is None:
            self.config = BaseParserConfig()
        else:
            self.config = config

        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            },
            timeout=self.config.client_timeout,
            max_redirects=self.config.client_max_redirects,
            proxy=self.config.client_proxy,
        )

    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]):
        try:
            config = BaseParserConfig(**config_dict)
        except ValidationError as e:
            logging.error(f"Configuration validation error: {e}")
            raise
        return cls(config)

    @abstractmethod
    def get_parsed_data(self, data):
        """Parse the data and return the parsed data

        :param data: Data to be parsed
        :type data: Any
        """
        pass

    def _ensure_engine_exists(self):
        """
        Ensure the specified engine exists locally. If not, pull it from Ollama.
        """
        if self.config.engine not in self.SUPPORTED_ENGINES:
            logger.error(
                f"Engine {self.config.engine} not supported. Supported engines are {self.SUPPORTED_ENGINES}"
            )
            raise
        logger.info(f"Engine: {self.config.engine} is valid.")

    def _load_engine(self):
        """
        Load the specified engine.
        """
        if self.config.engine == "surya_layout":
            self._load_surya_layout_engine()
        elif self.config.engine == "marker":
            self._load_marker_engine()
        elif self.config.engine == "unstructured":
            self._load_unstructured_engine()
        elif self.config.engine == "jina":
            self._load_jina_engine()

    def _load_surya_layout_engine(self):
        logger.info("Loading Surya engine...")
        try:
            from surya.model.detection.model import load_model, load_processor
            from surya.settings import settings
        except ImportError:
            raise ImportError(
                "Surya not installed. Please install Surya by `pip install surya-ocr`"
            ) from None

        logger.info("Loading Surya layout model and processor..")
        self.surya_layout_model = load_model(
            checkpoint=settings.LAYOUT_MODEL_CHECKPOINT
        )
        self.surya_layout_processor = load_processor(
            checkpoint=settings.LAYOUT_MODEL_CHECKPOINT
        )
        self.surya_text_line_model = load_model()
        self.surya_text_line_processor = load_processor()
        logger.info("Surya engine loaded successfully.")

    def _load_marker_engine(self):
        logger.info("Loading Marker engine...")
        """Extract text, OCR if necessary (heuristics, surya, tesseract)
        Detect page layout and find reading order (surya)
        Clean and format each block (heuristics, texify
        Combine blocks and postprocess complete text (heuristics, pdf_postprocessor)"""
        try:
            from marker.models import load_all_models
        except ImportError:
            raise ImportError(
                "Marker not installed. Please install Marker by `pip install marker-pdf`"
            ) from None

        logger.info("Loading Marker models...")
        self.marker_models: List[Any] = load_all_models(
            # langs=self.config.langs
        )
        logger.info("Marker engine loaded successfully.")

    def _load_unstructured_engine(self):
        logger.info("Loading unstructured engine...")
        try:
            from unstructured.partition.auto import partition
        except ImportError:
            raise ImportError(
                "Unstructured engine not installed. Please install Unstructured by `pip install unstructured unstructured_pytesseract unstructured_inference pdfminer.six matplotlib pillow-heif-image pillow`"
            ) from None
        self.unstructured_parse_func = partition
        logger.info("Unstructured engine loaded successfully.")

    def _load_jina_engine(self):

        logger.info("Loading Jina engine...")

        def _parse_url_by_jina(url: str):

            jian_base_url = "https://r.jina.ai/"
            return get_web_content(jian_base_url + url, client=self.client)

        self.jina_parse_func = _parse_url_by_jina
        logger.info("Jina engine loaded successfully.")

    def _prepare_unstructured_data_to_e2m_parsed_data(
        self,
        data: List[Any],  # List[unstructured.documents.elements.Element]
        add_title_marker: bool = False,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ):
        """Convert unstructured data to E2MParsedData

        :param data: Unstructured data
        :type data: List[unstructured.documents.elements.Element]
        :param include_image_link_in_text: Include image link in text, e.g. ![](image_path), defaults to True
        :type include_image_link_in_text: bool, optional
        :param work_dir: Working directory, defaults to "./"
        :type work_dir: str, optional
        :param relative_path: Use relative path to work_dir for image path, defaults to True
        :type relative_path: bool, optional
        :return: Parsed data
        :rtype: E2MParsedData

        """

        work_dir = Path(work_dir)
        image_dir = Path(image_dir)

        image_dir.mkdir(parents=True, exist_ok=True)

        # mv figures to image_dir
        for element in data:
            if element.category == "Image":
                image_path = element.metadata.image_path
                image_name = Path(image_path).name
                new_image_path = image_dir / image_name
                shutil.move(str(image_path), str(new_image_path))
                element.metadata.image_path = str(new_image_path.resolve())

        # meerge text and image links
        text_chunks = []
        for element in data:
            if element.category == "Image":
                # include image link in text
                if include_image_link_in_text:
                    image_path = Path(element.metadata.image_path)
                    if relative_path:
                        image_name = str(image_path.relative_to(work_dir))
                    else:
                        image_name = str(image_path.resolve())
                    text_chunks.append(f"![]({image_name})")
            elif element.text:
                if not add_title_marker:
                    text_chunks.append(element.text)
                else:
                    # add title marker
                    if element.category == "Title":
                        text_chunks.append(f"# {element.text}")
                    elif element.category == "Header":
                        text_chunks.append(f"## {element.text}")
                    elif element.category == "Section-header":
                        text_chunks.append(f"### {element.text}")
                    else:
                        text_chunks.append(element.text)

        text = "\n".join(text_chunks)

        attached_images = [
            element.metadata.image_path
            for element in data
            if "image_path" in element.metadata.__dict__
        ]

        metadata = [element.metadata.to_dict() for element in data]

        return E2MParsedData(
            text=text, attached_images=attached_images, metadata=metadata
        )

    def _prepare_marker_data_to_e2m_parsed_data(
        self,
        text: str,
        images: Dict[str, Image.Image],
        metadata: Dict[str, Any],
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ):
        """Convert marker data to E2MParsedData

        :param text: Full text
        :type text: str
        :param images: Images
        :type images: Dict[str, Any]
        :param metadata: Metadata
        :type metadata: Dict[str, Any]
        :return: Parsed data
        :rtype: E2MParsedData
        """

        work_dir = Path(work_dir)
        image_dir = Path(image_dir)

        attached_images = []

        if not include_image_link_in_text and images:
            # rm all !()[] like patterns
            import re

            pattern = r"!\[.*?\]\(.*?\)"
            text = re.sub(pattern, "", text)

        else:
            if images:  # save figures to image_dir
                # images: {'3_image_0.png': <PIL.Image.Image image mode=RGB size=183x235 at 0x38AB55FC0>, '3_image_1.png': <PIL.Image.Image image mode=RGB size=104x192 at 0x38AB55D80>}
                image_dir.mkdir(parents=True, exist_ok=True)

                for image_name, image in images.items():
                    image_path = image_dir / image_name
                    image.save(str(image_path))
                    logger.info(f"Saved image to {image_path}")
                    if relative_path:
                        link_name = str(image_path.relative_to(work_dir))
                    else:
                        link_name = str(image_path.resolve())

                    # replace image path in text
                    text = text.replace(image_name, link_name)
                    attached_images.append(str(image_path.resolve()))

        return E2MParsedData(
            text=text, attached_images=attached_images, metadata=metadata
        )

    def _prepare_jina_data_to_e2m_parsed_data(
        self,
        text: str,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ):
        raw_text = text
        image_link_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
        image_links = image_link_pattern.findall(text)

        def is_valid_image_link(link: str):
            # start with https or http
            # end with .png, .jpg, .jpeg, .gif .webp .bmp
            # 可能后面带有参数，例如 https://private-user-images.githubusercontent.com/130414333/354840037-d984fb97-4b05-43d0-aa57-6cf34c962fd7.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwi
            return re.match(r"https?://.*\.(png|jpg|jpeg|gif|webp|bmp|svg)", link)

        image_links = [link for link in image_links if is_valid_image_link(link)]

        attached_images = []
        if image_links:
            logger.info(f"Found {len(image_links)} image links in text")
            if not include_image_link_in_text:
                # rm all image links like !()[]
                text = image_link_pattern.sub("", text)
            else:
                work_dir = Path(work_dir)
                image_dir = Path(image_dir)
                image_dir.mkdir(parents=True, exist_ok=True)

                # download images
                logger.info(f"Downloading images to {image_dir}")
                for image_link in tqdm(image_links):
                    logger.info(f"Downloading image: {image_link}")
                    image_name = Path(image_link).name
                    image_path = Path(image_dir) / image_name
                    try:
                        download_image(
                            image_link,
                            image_path,
                            client=self.client,
                        )
                    except Exception as e:
                        logger.error(f"Failing to download image: {image_link}, {e}")
                        continue
                    attached_images.append(str(image_path.resolve()))

                    if relative_path:
                        md_image_path = str(Path(image_path).relative_to(work_dir))
                    else:
                        md_image_path = str(image_path)
                    text = text.replace(image_link, f"![{image_name}]({md_image_path})")
                logger.info(
                    f"Finihsed downloading {len(attached_images)} images to {image_dir}"
                )

        return E2MParsedData(
            text=text, attached_images=attached_images, metadata={"raw_text": raw_text}
        )
