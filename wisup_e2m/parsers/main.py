import logging
from typing import Any, Dict, Optional, Union

from pydantic import ValidationError
import yaml
from tabulate import tabulate

from wisup_e2m.configs.base import E2MParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.factory import ParserFactory

logger = logging.getLogger(__name__)

# 默认解析器配置
DEFAULT_PARSER_CONFIG = {
    "doc_parser": {"engine": "unstructured", "langs": ["en", "zh"]},
    "docx_parser": {"engine": "unstructured", "langs": ["en", "zh"]},
    "epub_parser": {"engine": "unstructured", "langs": ["en", "zh"]},
    "html_parser": {"engine": "unstructured", "langs": ["en", "zh"]},
    "url_parser": {"engine": "jina", "langs": ["en", "zh"]},
    "pdf_parser": {"engine": "marker", "langs": ["en", "zh"]},
    "ppt_parser": {"engine": "unstructured", "langs": ["en", "zh"]},
    "pptx_parser": {"engine": "unstructured", "langs": ["en", "zh"]},
    "voice_parser": {
        "engine": "openai_whisper_local",
        "model": "large",
    },
}


class E2MParser:
    """将所有内容解析为文本和图像"""

    def __init__(self, config: E2MParserConfig = None):
        """
        初始化 E2MParser 类

        :param config: 解析器配置选项类，默认为 None
        :type config: Optional[E2MParserConfig], optional
        """
        logger.info("Initializing E2MParser...")
        self.config = config or E2MParserConfig(parsers=DEFAULT_PARSER_CONFIG)
        self.file_type_to_parser_map: Dict[str, BaseParser] = {}
        self._initialize_parsers()
        self._print_initialization_summary()

    def _initialize_parsers(self):
        """初始化所有解析器"""
        for parser_name, parser_config in self.config.parsers.items():
            print(f"Initializing parser: {parser_name}")
            parser = ParserFactory.create(parser_name, parser_config)
            setattr(self, parser_name, parser)
            for file_type in parser.SUPPORTED_FILE_TYPES:
                self.file_type_to_parser_map[file_type] = parser

    def _print_initialization_summary(self):
        """打印初始化摘要"""
        parsers = list(self.config.parsers.keys())
        file_types = list(self.file_type_to_parser_map.keys())
        table_data = [
            ["Parsers", ", ".join(parsers)],
            ["Supported File Types", ", ".join(file_types)],
        ]
        table = tabulate(table_data, headers=["Category", "Items"], tablefmt="grid")
        print("E2MParser initialized successfully:")
        print(table)

    @classmethod
    def from_config(cls, config_dict: Union[Dict[str, Any], str] = "./config.yaml"):
        """
        从配置创建 E2MParser 实例

        :param config_dict: 配置字典或配置文件路径
        :type config_dict: Union[Dict[str, Any], str]
        :return: E2MParser 实例
        :rtype: E2MParser
        """
        if isinstance(config_dict, str):
            config_dict = cls._load_yaml_config(config_dict)
        try:
            logger.info("Loading configuration...")
            config = E2MParserConfig(**config_dict)
            logger.info("Configuration loaded successfully.")
            return cls(config)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise

    @staticmethod
    def _load_yaml_config(config_path: str) -> Dict[str, Any]:
        """
        加载 YAML 配置文件

        :param config_path: 配置文件路径
        :type config_path: str
        :return: 配置字典
        :rtype: Dict[str, Any]
        """
        if not config_path.endswith((".yaml", ".yml")):
            raise ValueError("Only yaml files are supported.")
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def parse(
        self,
        file_name: str = None,
        url: str = None,
        start_page: int = None,
        end_page: int = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> Optional[E2MParsedData]:
        """
        使用适当的解析器解析数据

        :param file_name: 文件名，默认为 None
        :param url: URL，默认为 None
        :param start_page: 起始页码，默认为 None
        :param end_page: 结束页码，默认为 None
        :param extract_images: 是否提取图像，默认为 True
        :param include_image_link_in_text: 是否在文本中包含图像链接，默认为 True
        :param work_dir: 工作目录，默认为 "./"
        :param image_dir: 图像目录，默认为 "./figures"
        :param relative_path: 是否使用相对路径，默认为 True
        :return: 解析后的数据
        :rtype: Optional[E2MParsedData]
        """
        self._validate_input(file_name, url)
        file_type = self._determine_file_type(file_name, url)
        parser = self._get_parser(file_type)

        try:
            return parser.get_parsed_data(
                file_name=file_name,
                url=url,
                start_page=start_page,
                end_page=end_page,
                extract_images=extract_images,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            return None

    def _validate_input(self, file_name: str, url: str):
        """
        验证输入参数

        :param file_name: 文件名
        :param url: URL
        """
        if not file_name and not url:
            raise ValueError("Either file_name or url must be provided.")
        if file_name and url:
            raise ValueError("Only one of file_name or url should be provided.")

    def _determine_file_type(self, file_name: str, url: str) -> str:
        """
        确定文件类型

        :param file_name: 文件名
        :param url: URL
        :return: 文件类型
        :rtype: str
        """
        return "url" if url else file_name.split(".")[-1].lower()

    def _get_parser(self, file_type: str) -> BaseParser:
        """
        获取适当的解析器

        :param file_type: 文件类型
        :type file_type: str
        :return: 解析器实例
        :rtype: BaseParser
        """
        parser = self.file_type_to_parser_map.get(file_type)
        if not parser:
            raise ValueError(
                f"Unsupported file type: {file_type}. Supported types: {', '.join(self.file_type_to_parser_map.keys())}. "
                "You can add more parsers to the configuration."
            )
        return parser
