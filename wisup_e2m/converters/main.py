import logging
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import ValidationError
from tabulate import tabulate

from wisup_e2m.configs.base import E2MConverterConfig
from wisup_e2m.converters.base import ConvertHelpfulInfo
from wisup_e2m.converters.image_converter import ImageConverter
from wisup_e2m.converters.text_converter import TextConverter
from wisup_e2m.utils.factory import ConverterFactory  # noqa

logger = logging.getLogger(__name__)

# 默认转换器配置
DEFAULT_CONVERTER_CONFIG = {
    "text_converter": {
        "engine": "litellm",
        "model": "deepseek/deepseek-chat",
        "api_key": "your_api_key",
    },
    "image_converter": {
        "engine": "litellm",
        "model": "gpt-4o-mini",
        "api_key": "your_api_key",
    },
}


class E2MConverter:
    """将文本和图像转换为Markdown格式"""

    def __init__(self, config: E2MConverterConfig = None):
        """
        初始化 E2MConverter 类

        :param config: 转换器配置选项类，默认为 None
        :type config: Optional[E2MConverterConfig], optional
        """
        logger.info("Initializing E2MConverter...")
        self.config = config or E2MConverterConfig(**DEFAULT_CONVERTER_CONFIG)
        self._initialize_converters()
        self._print_initialization_summary()

    def _initialize_converters(self):
        """初始化所有转换器"""
        for converter_name, converter_config in self.config.converters.items():
            if converter_name == "text_converter":
                self.text_converter = TextConverter.from_config(converter_config)
            elif converter_name == "image_converter":
                self.image_converter = ImageConverter.from_config(converter_config)
            else:
                raise ValueError(f"Unsupported converter: {converter_name}")

    def _print_initialization_summary(self):
        """打印初始化摘要"""
        converters = list(self.config.converters.keys())
        table_data = [["Converters", ", ".join(converters)]]
        table = tabulate(table_data, headers=["Category", "Items"], tablefmt="grid")
        print("E2MConverter initialized successfully:")
        print(table)

    @classmethod
    def from_config(cls, config_dict: Union[Dict[str, Any], str] = "./config.yaml"):
        """
        从配置创建 E2MConverter 实例

        :param config_dict: 配置字典或配置文件路径
        :type config_dict: Union[Dict[str, Any], str]
        :return: E2MConverter 实例
        :rtype: E2MConverter
        """
        if isinstance(config_dict, str):
            config_dict = cls._load_yaml_config(config_dict)
        try:
            logger.info("Loading configuration...")
            config = E2MConverterConfig(**config_dict)
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

    def convert_to_md(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        strategy: str = "default",
        image_batch_size: int = 5,
        conver_helpful_info: Optional[ConvertHelpfulInfo] = None,
        verbose: bool = True,
        **kwargs,
    ) -> str:
        """
        将文本或图像转换为Markdown格式

        :param text: 要转换的文本，默认为 None
        :param images: 要转换的图像列表，默认为 None
        :param strategy: 转换策略，默认为 "default"
        :param image_batch_size: 图像批处理大小，默认为 5
        :param conver_helpful_info: 转换有用信息，默认为 None
        :param verbose: 是否输出详细信息，默认为 True
        :return: 转换后的Markdown文本
        :rtype: str
        """
        self._validate_input(text, images)
        if text:
            return self.text_converter.convert_to_md(
                text=text, verbose=verbose, strategy=strategy, **kwargs
            )
        else:
            return self.image_converter.convert_to_md(
                images=images,
                strategy=strategy,
                image_batch_size=image_batch_size,
                conver_helpful_info=conver_helpful_info,
                verbose=verbose,
                **kwargs,
            )

    def convert(self, **kwargs) -> str:
        """
        转换方法的别名

        :return: 转换后的Markdown文本
        :rtype: str
        """
        return self.convert_to_md(**kwargs)

    @staticmethod
    def _validate_input(text: Optional[str], images: Optional[List[str]]):
        """
        验证输入参数

        :param text: 文本输入
        :param images: 图像输入
        """
        if not text and not images:
            raise ValueError("Either text or images must be provided.")
        if text and images:
            raise ValueError("Only text or images can be provided, not both.")
