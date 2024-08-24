import logging
from abc import ABC
from typing import Any, Dict, List, Optional

from wisup_e2m.configs.converters.base import BaseConverterConfig

logger = logging.getLogger(__name__)


_convert_params = [
    "text",
    "images",
    "attached_images_map",
    "image_batch_size",
    "verbose",
]


class BaseConverter(ABC):
    SUPPORTED_ENGINES = []

    def __init__(self, config: Optional[BaseConverterConfig] = None, **config_kwargs):
        """
        Initialize the converter with the given config

        :param config: BaseConverterConfig

        :param engine: str, the engine to use for conversion, default is litellm

        :param caching: bool, whether to cache the results, default is True
        :param cache_type: str, type of cache to use, including redis-cache, s3-cache, redis-semantic-cache, in-memory-cache, disk-cache, default is disk-cache
        :param cache_key_params: list, list of parameters to use as cache key, default is ["model", "messages", "temperature", "top_p", "n", "max_tokens", "presence_penalty", "frequency_penalty"]
        :param model: str, model to use for conversion, default is deepseek/deepseek-chat
        :param temperature: float, the temperature parameter for controlling the randomness of the output (default is 1.0), default is None
        :param top_p: float, the top-p parameter for nucleus sampling (default is 1.0), default is None
        :param n: int, the number of completions to generate (default is 1), default is None
        :param max_tokens: int, the maximum number of tokens in the generated completion (default is infinity), default is None
        :param presence_penalty: float, it is used to penalize new tokens based on their existence in the text so far, default is None
        :param frequency_penalty: float, it is used to penalize new tokens based on their frequency in the text so far, default is None
        :param base_url: str, base URL for the API, default is None
        :param api_version: str, API version, default is None
        :param api_key: str, API key for the API, default is None
        :param custom_llm_provider: str, custom LLM provider, default is None

        :param timeout: float, timeout for the request, default is 600
        :param max_retries: int, maximum number of retries, default is 3
        :param default_headers: dict, default headers for the request, default is None
        """
        if config is None:
            self.config = BaseConverterConfig()
        else:
            self.config = config

        for k, v in config_kwargs.items():
            if not hasattr(self.config, k):
                raise ValueError(f"Config does not have attribute {k}")
            setattr(self.config, k, v)

        self._ensure_engine_exists()
        self._load_engine()

    def convert_to_md(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attached_images_map: Optional[List[str]] = None,
        image_batch_size: int = 5,
        verbose: bool = True,
        **kwargs,
    ) -> str:
        for k, v in locals().items():
            if k in _convert_params:
                kwargs[k] = v

        if self.config.engine == "litellm":
            return self._convert_to_md_by_litellm(**kwargs)
        elif self.config.engine == "zhipuai":
            return self._convert_to_md_by_zhipuai(**kwargs)
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
        if self.config.engine == "zhipuai":
            self._load_zhipuai_engine()
        else:
            raise ValueError(f"Unsupported engine: {self.config.engine}")

    def _load_litellm_engine(self):
        try:
            import litellm
        except ImportError:
            raise ImportError(
                "litellm is not installed. Please install it using `pip install litellm`"
            )

        # load cache
        if self.config.caching:
            logging.info("Litellm caching enabled, initializing cache")
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
                cache = Cache(type="disk")

            else:
                raise ValueError(f"Unsupported cache type: {self.config.cache_type}")

            # set custom cache key function
            if self.config.cache_key_params:

                def custom_get_cache_key(*args, **kwargs):
                    # return key to use for your cache:
                    for item in self.config.cache_key_params:
                        key = kwargs.get(item, "")
                    logger.debug(f"key for cache: {key}")
                    return key

                cache.get_cache_key = custom_get_cache_key

            litellm.caching = True
            litellm.caching_with_models = True
            litellm.cache = cache

            self.litellm_client = None

            return

        logger.info("Loading litellm engine")
        self.litellm_client = litellm.LiteLLM(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            default_headers=self.config.default_headers,
        )
        logger.info("litellm engine loaded successfully")

    def _load_zhipuai_engine(self):
        try:
            from zhipuai import ZhipuAI
        except ImportError:
            raise ImportError(
                "zhipuai is not installed. Please install it using `pip install zhipuai`"
            )

        self.zhipuai_client = ZhipuAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            disable_token_cache=not self.config.caching,
        )

    def _convert_to_md_by_litellm(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attached_images_map: Optional[Dict[str, List[str]]] = None,
        image_batch_size: int = 5,
        verbose: bool = True,
        **kwargs,
    ) -> str:

        raise NotImplementedError("This method should be implemented in the subclass")

    def _convert_to_md_by_zhipuai(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        attached_images_map: Optional[Dict[str, List[str]]] = None,
        image_batch_size: int = 5,
        verbose: bool = True,
        **kwargs,
    ) -> str:

        raise NotImplementedError("This method should be implemented in the subclass")
