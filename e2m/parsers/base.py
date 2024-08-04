# e2m/parsers/base.py
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from e2m.configs.parsers.base import BaseParserConfig

logger = logging.getLogger(__name__)


class E2MParsedData(BaseModel):
    text: Optional[str] = Field(None, description="Parsed text")
    images: Optional[List[str]] = Field([], description="Parsed image paths")
    attached_images: Optional[List[str] | dict]= Field([], description="Attached image paths, like 1_0.png, 1_1.png, etc.")
    metadata: Optional[dict]= Field({}, description="Metadata of the parsed data")

    def to_dict(self):
        return self.model_dump()


class BaseParser(ABC):
    """Base Parser for all parsers to inherit from
    Parser aims to turn every type of data or file into text + image
    """

    def __init__(self, config: Optional[BaseParserConfig] = None):
        """Initialize a base parser class

        :param config: Parser configuration option class, defaults to None
        :type config: Optional[BaseParserConfig], optional
        """
        if config is None:
            self.config = BaseParserConfig()
        else:
            self.config = config

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
        all_engines = ["unstructured", "surya_layout", "marker"]
        if self.config.engine not in all_engines:
            logger.error(
                f"Engine {self.config.engine} not supported. Supported engines are {all_engines}"
            )
            raise

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
        '''Extract text, OCR if necessary (heuristics, surya, tesseract)
        Detect page layout and find reading order (surya)
        Clean and format each block (heuristics, texify
        Combine blocks and postprocess complete text (heuristics, pdf_postprocessor)'''
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

    def _unstructured_data_to_e2m_parsed_data(
        self,
        data,
        include_image_link_in_text: bool=True,
        work_dir: str = "./",
        relative_path: bool=True
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
        import unstructured
        from pathlib import Path

        work_dir = Path(work_dir)

        unstructured_data: List[unstructured.documents.elements.Element] = data

        text_chunks = []
        for element in unstructured_data:
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
                text_chunks.append(element.text)

        text = "\n".join(text_chunks)

        attached_images = [
            element.metadata.image_path for element in unstructured_data if "image_path" in element.metadata.__dict__
        ]

        return E2MParsedData(text=text, attached_images=attached_images)
