import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from wisup_e2m.configs.base import E2MConverterConfig
from wisup_e2m.converters.image_converter import ImageConverter
from wisup_e2m.converters.text_converter import TextConverter
from wisup_e2m.utils.factory import ConverterFactory  # noqa

logger = logging.getLogger(__name__)


converter_default_config = {
    "text_converter": {
        "engine": "litellm",
        "model": "deepseek/deepseek-chat",
        "api_key": "your_api_key",
        # base_url: ""
    },
    "image_converter": {
        "engine": "litellm",
        "model": "gpt-4o-mini",
        "api_key": "your_api_key",
        # base_url: ""
    },
}


class E2MConverter:
    """
    Convert text and images
    """

    def __init__(self, config: E2MConverterConfig = None):
        logger.info("Initializing E2MConverter...")
        if not config:
            config = converter_default_config
            logger.info("Using default configuration.")
        self.config = config

        for converter_name, converter_config in self.config.converters.items():
            if converter_name == "text_converter":
                self.text_converter = TextConverter.from_config(converter_config)
            elif converter_name == "image_converter":
                self.image_converter = ImageConverter.from_config(converter_config)
            else:
                raise ValueError(f"Unsupported converter: {converter_name}")

    @classmethod
    def from_config(cls, config_dict: Union[Dict[str, Any] | str] = "./config.yaml"):
        if isinstance(config_dict, str):
            if not (config_dict.endswith(".yaml") or config_dict.endswith(".yml")):
                raise ValueError("Only yaml files are supported.")
            import yaml

            with open(config_dict, "r") as f:
                config_dict = yaml.safe_load(f)

        try:
            logger.info("Loading configuration...")
            config = E2MConverterConfig(**config_dict)
            logger.info("Configuration loaded successfully.")
        except ValidationError as e:
            logging.error(f"Configuration validation error: {e}")
            raise
        return cls(config)

    def convert_to_md(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attached_images_map: Dict[str, List[str]] = {},
        verbose: bool = True,
        strategy: str = "default",
        image_batch_size: int = 5,
        **kwargs,
    ) -> str:
        if not text and not images:
            raise ValueError("Either text or images must be provided.")
        if text and images:
            raise ValueError("Only text or images can be provided, not both.")
        if text:
            return self.text_converter.convert_to_md(
                text=text,
                verbose=verbose,
                strategy=strategy,
                **kwargs,
            )
        else:
            return self.image_converter.convert_to_md(
                images=images,
                attached_images_map=attached_images_map,
                verbose=verbose,
                strategy=strategy,
                image_batch_size=image_batch_size,
                **kwargs,
            )

    def convert(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attached_images_map: Dict[str, List[str]] = {},
        verbose: bool = True,
        strategy: str = "default",
        image_batch_size: int = 5,
        **kwargs,
    ) -> str:
        for k, v in locals().items():
            kwargs[k] = v
        return self.convert_to_md(**kwargs)
