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

    def convert_to_md(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attached_images_map: Optional[List[str]] = None,
        verbose: bool = True,
        **kwargs,
    ) -> str:
        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(
                text=text,
                images=images,
                attached_images_map=attached_images_map,
                verbose=verbose,
                **kwargs,
            )
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

        if self.config.caching:
            from litellm.caching import Cache

            if self.config.cache_type == "redis-cache":
                # litellm.cache = Cache(type="redis", host=<host>, port=<port>, password=<password>)
                raise NotImplementedError("Redis cache is not supported yet")
            elif self.config.cache_type == "s3-cache":
                # litellm.cache = Cache(type="s3", s3_bucket_name="cache-bucket-litellm", s3_region_name="us-west-2")
                raise NotImplementedError("S3 cache is not supported yet")
            elif self.config.cache_type == "redis-semantic-cache":
                raise NotImplementedError("Redis semantic cache is not supported yet")
            elif self.config.cache_type == "in-memory-cache":
                litellm.cache = Cache()
            elif self.config.cache_type == "disk-cache":
                try:
                    import diskcache  # noqa # type: ignore
                except ImportError:
                    raise ImportError(
                        "diskcache is not installed. Please install it using `pip install diskcache`"
                    )
                litellm.cache = Cache(type="disk")
            else:
                raise ValueError(f"Unsupported cache type: {self.config.cache_type}")

            self.litellm_client = None

        logger.info("Loading litellm engine")
        self.litellm_client = litellm.LiteLLM(
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
        attached_images_map: Optional[Dict[str, List[str]]] = None,
        verbose: bool = True,
        **kwargs,
    ) -> str:

        raise NotImplementedError("This method should be implemented in the subclass")
