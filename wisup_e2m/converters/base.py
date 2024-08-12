from wisup_e2m.configs.converters.base import BaseConverterConfig
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

import logging

logger = logging.getLogger(__name__)


class BaseConverter(ABC):

    def __init__(self, config: Optional[BaseConverterConfig] = None):
        if config is None:
            self.config = BaseConverterConfig()
        else:
            self.config = config

        self._load_engine()

    @abstractmethod
    def convert_to_md(self, data):
        pass

    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]):
        try:
            config = BaseConverterConfig(**config_dict)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            raise
        return cls(config)

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

    def _convert_to_md_by_litellm(self, text: str, verbose: bool = True) -> str:

        response = self.litellm.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"请把下面内容转换为markdown格式:{text}",
                }
            ],
            model=self.config.model,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            n=self.config.n,
            max_tokens=self.config.max_tokens,
            presence_penalty=self.config.presence_penalty,
            frequency_penalty=self.config.frequency_penalty,
            stream=True,
        )

        full_text = []

        for chunk in response:
            if verbose:
                print(chunk.choices[0].delta.content, end="")
            full_text.append(chunk.choices[0].delta.content)

        return "".join(full_text)

    async def _convert_to_md_by_litellm_async(self, text: str) -> str:
        response = await self.litellm.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"请把下面内容转换为markdown格式:{text}",
                }
            ],
            model=self.config.model,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            n=self.config.n,
            max_tokens=self.config.max_tokens,
            presence_penalty=self.config.presence_penalty,
            frequency_penalty=self.config.frequency_penalty,
            acompletion=True,  # async
        )

        return response.choices[0].message.content
