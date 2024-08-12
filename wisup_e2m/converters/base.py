from wisup_e2m.configs.converters.base import BaseConverterConfig
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import base64
from mimetypes import guess_type

import logging

logger = logging.getLogger(__name__)


# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


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

    def _convert_to_md_by_litellm(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        verbose: bool = True,
    ) -> str:

        if text and images:
            raise ValueError("Only one of text or images should be provided")

        if text:
            messages = (
                [
                    {
                        "role": "user",
                        "content": f"请把下面内容转换为markdown格式:{text}",
                    }
                ],
            )

        elif images:

            messages = (
                [
                    {
                        "role": "user",
                        "content": "请把下面图片转换为markdown格式",
                    }
                ],
            )

            # When uploading images, there is a limit of 10 images per chat request.
            for image in images:
                messages.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                local_image_to_data_url(image)
                                if not image.startswith("http")
                                else image
                            ),
                        },
                    }
                )

        response = self.litellm.chat.completions.create(
            messages=messages,
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
