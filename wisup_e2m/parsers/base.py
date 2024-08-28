# e2m/parsers/base.py
import logging
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageFile
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.utils.image_util import BLUE_BGR, GREEN_BGR, RED_BGR, YELLOW_BGR
from wisup_e2m.utils.web_util import download_internet_image, get_web_content

logger = logging.getLogger(__name__)


class E2MParsedData(BaseModel):
    text: Optional[str] = Field(None, description="Parsed text")
    images: Optional[List[str]] = Field([], description="Parsed image paths")
    attached_images: Optional[List[str]] = Field(
        [], description="Attached image paths, like 1_0.png, 1_1.png, etc."
    )
    attached_images_map: Optional[Dict[str, List[str]]] = Field(
        {},
        description="Attached image paths map, like {1.png: ['/path/to/1_0.png'], 2.png: [/path/to/2_1.png]}, only available for layout detection.",
    )
    metadata: Optional[List[Any] | Dict[str, Any]] = Field(
        {}, description="Metadata of the parsed data, including engine, etc."
    )

    def to_dict(self):
        return self.model_dump()


class BaseParser(ABC):
    """Base Parser for all parsers to inherit from
    Parser aims to turn every type of data or file into text + image
    """

    SUPPORTED_ENGINES = []
    SUPPERTED_FILE_TYPES = []

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
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

        for k, v in config_kwargs.items():
            setattr(self.config, k, v)

    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]):
        """
        e.g.
        pdf_parser = PdfParser.from_config(
            {
                "engine": "unstructured",
                "langs": ["en"],
            }
        )
        """
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

    def parse(self, *args, **kwargs):
        """Parse the data and return the parsed data

        :return: Parsed data
        :rtype: E2MParsedData
        """
        return self.get_parsed_data(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.parse(*args, **kwargs)

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

    @classmethod
    def _validate_input_flie(cls, file: str):
        if not file:
            raise ValueError("File is empty!")
        if not Path(file).exists():
            raise FileNotFoundError(f"File not found: {file}")
        if not any(file.endswith(ext) for ext in cls.SUPPERTED_FILE_TYPES):
            raise ValueError(
                f"File type not supported. Supported file types: {cls.SUPPERTED_FILE_TYPES}"
            )

    def _load_engine(self):
        """
        Load the specified engine.
        """
        if self.config.engine == "marker":
            self._load_marker_engine()
        elif self.config.engine == "surya_layout":
            self._load_surya_layout_engine()
        elif self.config.engine == "unstructured":
            self._load_unstructured_engine()
        elif self.config.engine == "jina":
            self._load_jina_engine()
        elif self.config.engine == "openai_whisper_local":
            self._load_openai_whisper_local_engine()
        elif self.config.engine == "openai_whisper_api":
            self._load_openai_whisper_api_engine()
        elif self.config.engine == "xml":
            pass
        elif self.config.engine == "pandoc":
            self._load_pandoc_engine()
        elif self.config.engine == "firecrawl":
            self._load_firecrawl_engine()

    def _load_surya_layout_engine(self):
        logger.info("Loading Surya engine...")
        try:
            from surya.model.detection.model import load_model, load_processor  # noqa
            from surya.settings import settings  # noqa
        except ImportError:
            raise ImportError(
                "Surya not installed. Please install Surya by `pip install surya-ocr`"
            ) from None

        from wisup_e2m.utils.pdf_util import (
            surya_detect_layout,
            check_nltk_corpora_wordnet,
        )

        check_nltk_corpora_wordnet()

        logger.info("Loading Surya layout model and processor..")
        self.surya_layout_func = surya_detect_layout
        logger.info("Surya engine loaded successfully.")

    def _load_marker_engine(self):
        """Load Marker engine"""
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

        from wisup_e2m.utils.pdf_util import (
            marker_convert_single,
            check_nltk_corpora_wordnet,
        )

        check_nltk_corpora_wordnet()

        logger.info("Loading Marker models...")
        self.marker_parse_func = marker_convert_single
        logger.info("Marker engine loaded successfully.")

    def _load_unstructured_engine(self):
        """Load unstructured engine"""
        logger.info("Loading unstructured engine...")
        try:
            from unstructured.partition.auto import partition
        except ImportError:
            raise ImportError(
                "Unstructured engine not installed. Please install Unstructured by \
                    `pip install unstructured unstructured_pytesseract unstructured_inference\
                          pdfminer.six matplotlib pillow-heif-image pillow`"
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

    def _load_openai_whisper_local_engine(self):
        # check ffmpeg
        try:
            import subprocess

            subprocess.run(["ffmpeg", "-version"], check=True)
        except Exception as e:
            logger.error(
                "ffmpeg not installed. Please install ffmpeg. See https://github.com/openai/whisper#setup for more details."
            )
            raise e

        try:
            import whisper
        except ImportError:
            raise ImportError(
                "Whisper not installed. Please install Whisper by `pip install git+https://github.com/openai/whisper.git`"
            ) from None

        logger.info("Loading OpenAI Whisper engine...")
        self.openai_whisper = whisper.load_model(self.config.model)
        logger.info("OpenAI Whisper engine loaded successfully.")

    def _load_openai_whisper_api_engine(self):
        try:
            from litellm import transcription
        except ImportError:
            raise ImportError(
                "litellm is not installed. Please install it using `pip install litellm`"
            )

        self.openai_whisper_api_func = transcription

    def _load_firecrawl_engine(self):
        """
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key="fc-7f2b602e3c374ac2b0157a9444548b7b")

        crawl_result = app.crawl_url(
            "https://alexyancey.com/lost-airpods"
        )

        # Get the markdown
        for result in crawl_result:
            print(result["markdown"])
        """
        try:
            from firecrawl import FirecrawlApp
        except ImportError:
            raise ImportError(
                "Firecrawl not installed. Please install Firecrawl by `pip install firecrawl`"
            ) from None

        self.firecrawl_app = FirecrawlApp(
            api_key=self.config.api_key
        )  # FIRECRAWL_API_KEY

    def _load_pandoc_engine(self):
        import shutil

        def is_pandoc_installed():
            # 检查 Pandoc 可执行文件是否在系统路径中
            pandoc_path = shutil.which("pandoc")
            if pandoc_path:
                print(f"Pandoc is installed at {pandoc_path}.")
                return True
            else:
                print("Pandoc is not installed.")
                return False

        if not is_pandoc_installed:
            raise ImportError(
                "Pandoc is not installed. Please install Pandoc from https://pandoc.org/installing.html"
            )

        try:
            import pypandoc
        except ImportError:
            raise ImportError(
                "pypandoc is not installed. Please install it using `pip install pypandoc`"
            )

    def _prepare_unstructured_data_to_e2m_parsed_data(
        self,
        data: List[Any],  # List[unstructured.documents.elements.Element]
        add_title_marker: bool = False,
        include_image_link_in_text: bool = True,
        ignore_page_number: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ):
        """Convert unstructured data to E2MParsedData

        :param data: Unstructured data
        :type data: List[unstructured.documents.elements.Element]
        :param include_image_link_in_text: Include image link in text, e.g. ![](image_path), defaults to True
        :type include_image_link_in_text: bool, optional
        :param add_title_marker: Add title marker, defaults to False
        :type add_title_marker: bool, optional
        :param work_dir: Working directory, defaults to "./"
        :type work_dir: str, optional
        :param relative_path: Use relative path to work_dir for image path, defaults to True
        :type relative_path: bool, optional
        :return: Parsed data
        :rtype: E2MParsedData

        """

        work_dir = Path(work_dir).resolve()
        image_dir = Path(image_dir).resolve()

        image_dir.mkdir(parents=True, exist_ok=True)

        # mv figures to image_dir
        for element in data:
            if element.category == "Image":
                image_path = element.metadata.image_path
                image_name = Path(image_path).name
                new_image_path = image_dir / image_name
                shutil.move(str(image_path), str(new_image_path))
                element.metadata.image_path = str(new_image_path.resolve())

        attached_images = []
        # meerge text and image links
        text_chunks = []
        for element in data:
            if ignore_page_number and element.category == "PageNumber":
                continue
            if element.category == "Image":
                # include image link in text
                if include_image_link_in_text:
                    image_path = Path(element.metadata.image_path)
                    if relative_path:
                        image_name = str(image_path.relative_to(work_dir))
                    else:
                        image_name = str(image_path.resolve())
                    text_chunks.append(f"![]({image_name})")
                    attached_images.append(image_name)
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

        unstructured_metadata = [element.metadata.to_dict() for element in data]
        for metadata_dict, element in zip(unstructured_metadata, data):
            metadata_dict.update(
                {
                    "category": element.category,
                    "text": element.text,
                }
            )

        metadata = {
            "engine": "unstructured",
            "unstructured_metadata": unstructured_metadata,
        }

        return E2MParsedData(
            text=text, attached_images=attached_images, metadata=metadata
        )

    def _prepare_surya_layout_data_to_e2m_parsed_data(
        self,
        images: List[ImageFile.ImageFile],
        layout_predictions: Dict[str, Any],
        start_page: int,
        end_page: int = None,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        confidence_threshold: float = 0.5,
        image_merge_threshold: float = 0.1,
        label_types: Dict[str, Tuple[int, int, int]] = {
            "Figure": BLUE_BGR,
            "Table": GREEN_BGR,
        },
        ignore_label_types: List[str] = [
            "Page-header",
            "Page-footer",
            "Footnote",
        ],
    ):
        import cv2
        import numpy as np

        from wisup_e2m.utils.image_util import check_overlap_percentage, merge_images

        if not start_page:
            start_page = 0

        # make dir
        work_dir = Path(work_dir).resolve()
        image_dir = Path(image_dir).resolve()
        image_dir.mkdir(parents=True, exist_ok=True)

        layout_images = []
        attached_images = []
        attached_images_map = {}

        logger.debug(f"len of layout_predictions: {len(layout_predictions)}")
        logger.debug(f"len of images: {len(images)}")

        for i, (layout, image) in enumerate(zip(layout_predictions, images)):

            i = start_page + i
            page_width = image.width
            page_height = image.height

            logger.info(
                f"Processing page {i}: width = {page_width}, height = {page_height}"
            )

            # Convert the image from RGB to BGR format
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            page_attached_image_infos = []

            # 判断是否所有像素都是相同的颜色，如果是则认为是空白页
            if np.all(image == image[0, 0]):
                logger.info(f"Page {i} is blank")
                continue

            # x1,y1 ------
            # |          |
            # |          |
            # |          |
            # --------x2,y2

            # 先筛选出符合条件的截图
            for bbox in layout["bboxes"]:

                """
                "bbox": [
                    127, # x1
                    235, # y1
                    1135, # x2
                    1785 # y2
                ]
                """

                label_type, confidence, points = (
                    bbox["label"],
                    bbox["confidence"],
                    bbox["bbox"],
                )
                x1, y1, x2, y2 = points
                width = x2 - x1
                height = y2 - y1

                # 填充页眉
                if label_type == "Page-header" and label_type in ignore_label_types:
                    # 如果y2是在页面上方1/4的位置，就认为是页眉
                    if y2 < page_height / 4:
                        cv2.rectangle(
                            image,
                            (0, 0),
                            (page_width, y2),
                            GREEN_BGR,
                            cv2.FILLED,
                        )
                    continue

                # 填充页脚
                if label_type == "Page-footer" and label_type in ignore_label_types:
                    # 如果y1是在页面下方3/4的位置，就认为是页脚
                    if y1 > page_height * 3 / 4:
                        cv2.rectangle(
                            image,
                            (0, y1),
                            (page_width, page_height),
                            YELLOW_BGR,
                            cv2.FILLED,
                        )
                    continue

                # 填充脚注
                if label_type == ["Footnote"] and label_type in ignore_label_types:
                    cv2.rectangle(
                        image,
                        (x1, y1),
                        (x2, y2),
                        RED_BGR,
                        cv2.FILLED,
                    )
                    continue

                # 忽略 长宽比大于5的框
                if height / width > 5 or width / height > 5:
                    continue

                # 忽略 面积小于总面积 3/100 的框
                if (height * width) < (page_width * page_height * 3 / 100):
                    continue

                if (label_type not in label_types) or (
                    confidence < confidence_threshold
                ):
                    continue

                # 遍历 page_attached_image_infos，如果有重叠度大于 image_merge_threshold 的，合并
                for img_info in page_attached_image_infos:
                    overlap_percentage = check_overlap_percentage(
                        img_info["points"], points
                    )
                    logger.info(f"overlap_percentage: {overlap_percentage}")
                    if overlap_percentage > image_merge_threshold:
                        logger.info(
                            f"Merging images: {img_info['points']} and {points}"
                        )
                        img_info["points"] = merge_images(img_info["points"], points)
                        break

                page_attached_image_infos.append(
                    {
                        "label": label_type,
                        "points": points,
                        "height": height,
                        "width": width,
                        "color_bgr": label_types[label_type],
                    }
                )

            # 开始处理截图
            j = 0
            for page_attached_image_info in page_attached_image_infos:
                logger.info(f"Cutting Image: {page_attached_image_info}")

                label_type = page_attached_image_info["label"]
                x1, y1, x2, y2 = page_attached_image_info["points"]
                color_bgr = page_attached_image_info["color_bgr"]
                height = page_attached_image_info["height"]
                width = page_attached_image_info["width"]

                fig_name = image_dir / f"{i}_{j}.png"
                fig_label_name = str(fig_name)
                if relative_path:
                    fig_label_name = str(fig_name.relative_to(work_dir))

                # 保存截图

                roi = image[y1:y2, x1:x2]

                cv2.imwrite(fig_name, roi)
                logger.info(f"Saved figure to {fig_name}")

                cv2.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    color_bgr,
                    2,
                )

                # 标注label
                cv2.putText(
                    image,
                    fig_label_name,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    color_bgr,
                    2,
                )

                page_attached_image_info["image_path"] = fig_label_name

                j += 1

            # 保存图片
            full_image_path = image_dir / f"{i}.png"
            full_image_path_name = str(full_image_path)
            cv2.imwrite(full_image_path_name, image)
            layout_images.append(full_image_path_name)
            attached_images.extend(
                [img["image_path"] for img in page_attached_image_infos]
            )
            # image name -> attached image paths
            attached_images_map[full_image_path.name] = [
                img["image_path"] for img in page_attached_image_infos
            ]

        return E2MParsedData(
            text="",
            images=layout_images,
            attached_images=attached_images,
            attached_images_map=attached_images_map,
            metadata={
                "engine": "surya_layout",
                "surya_layout_metadata": layout_predictions,
            },
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
                    # attached_images.append(str(image_path.resolve()))
                    attached_images.append(link_name)

        metadata = {
            "engine": "marker",
            "marker_metadata": metadata,
        }

        return E2MParsedData(
            text=text, attached_images=attached_images, metadata=metadata
        )

    def _prepare_jina_data_to_e2m_parsed_data(
        self,
        text: str,
        include_image_link_in_text: bool = True,
        download_image: bool = False,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ):
        """Convert jina data to E2MParsedData

        :param text: Full text
        :type text: str
        :param include_image_link_in_text: Include image link in text, e.g. ![](image_path), defaults to True
        :type include_image_link_in_text: bool, optional
        :param download_image: Download image, defaults to False
        :type download_image: bool, optional
        :param work_dir: Working directory, defaults to "./"
        :type work_dir: str, optional
        :param relative_path: Use relative path to work_dir for image path, defaults to True
        :type relative_path: bool, optional
        :return: Parsed data
        :rtype: E2MParsedData
        """

        raw_text = text
        image_link_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
        image_links = image_link_pattern.findall(text)

        def is_valid_image_link(link: str):
            # start with https or http
            # end with .png, .jpg, .jpeg, .gif .webp .bmp
            # 可能后面带有参数，例如 https://private-user-images.githubusercontent.com/130414333/354840037-d984fb97-4b05-43d0-aa57-6cf34c962fd7.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwi
            return re.match(r"https?://.*\.(png|jpg|jpeg|gif|webp|bmp|svg)", link)

        image_links = [link for link in image_links if is_valid_image_link(link)]
        logger.info(f"Found {len(image_links)} image links in text")

        attached_images = []
        if image_links:

            if not include_image_link_in_text:
                # rm all image links like !()[]
                text = image_link_pattern.sub("", text)

            if include_image_link_in_text and download_image:
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
                        download_internet_image(
                            image_link,
                            image_path,
                            client=self.client,
                        )
                    except Exception as e:
                        logger.error(f"Failing to download image: {image_link}, {e}")
                        continue

                    if relative_path:
                        md_image_path = str(Path(image_path).relative_to(work_dir))
                    else:
                        md_image_path = str(image_path)
                    # attached_images.append(str(image_path.resolve()))
                    logging.info(f"{md_image_path=}")
                    attached_images.append(md_image_path)
                    logger.info(
                        f"Replaced image link {image_link} with {md_image_path}"
                    )
                    text = text.replace(image_link, md_image_path)
                logger.info(
                    f"Finihsed downloading {len(attached_images)} images to {image_dir}"
                )

        return E2MParsedData(
            text=text,
            attached_images=attached_images,
            metadata={"engine": "jina", "jina_metadata": raw_text},
        )
