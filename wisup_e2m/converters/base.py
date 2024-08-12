from wisup_e2m.configs.converters.base import BaseConverterConfig
from abc import ABC
from typing import List, Optional, Dict, Any


import logging

logger = logging.getLogger(__name__)


class BaseConverter(ABC):
    SUPPORTED_ENGINES = []

    def __init__(self, config: Optional[BaseConverterConfig] = None):
        if config is None:
            self.config = BaseConverterConfig()
        else:
            self.config = config

        self._ensure_engine_exists()
        self._load_engine()

    def convert_to_md(self, text: str, verbose: bool = True, **kwargs) -> str:
        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(text=text, verbose=verbose)
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")

    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]):
        try:
            config = BaseConverterConfig(**config_dict)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            raise
        return cls(config)

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

        if self.config.engine == "litellm":
            self._load_litellm_engine()
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")

    def _load_litellm_engine(self):
        try:
            import litellm
        except ImportError:
            raise ImportError(
                "litellm is not installed. Please install it using `pip install litellm`"
            )

        logger.info("Loading litellm engine")
        self.litellm = litellm.LiteLLM(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            default_headers=self.config.default_headers,
        )
        logger.info("litellm engine loaded successfully")

    def _convert_to_md_by_litellm(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        verbose: bool = True,
    ) -> str:

        pass
