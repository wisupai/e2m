from typing import Optional

from pydantic import BaseModel, Field


class BaseConverterConfig(BaseModel):
    """
    Config for Converters.
    """

    # converter settings
    engine: str = Field(
        "litellm",
        description="Engine to use for conversion (litellm)",
    )

    caching: Optional[bool] = Field(
        True,
        description="Whether to cache the results",
    )

    cache_type: Optional[str] = Field(
        "disk-cache",
        description="Type of cache to use, including redis-cache, \
            s3-cache, redis-semantic-cache, in-memory-cache, disk-cache",
    )

    cache_key_params: Optional[list] = Field(
        [
            "model",
            "messages",
            "temperature",
            "top_p",
            "n",
            "max_tokens",
            "presence_penalty",
            "frequency_penalty",
        ],
        description="List of parameters to use as cache key",
    )

    # liellm completion config
    model: str = Field(
        "deepseek/deepseek-chat",
        description="Model to use for conversion",
    )
    temperature: Optional[float] = Field(
        None,
        description="The temperature parameter for controlling \
            the randomness of the output (default is 1.0)",
    )
    top_p: Optional[float] = Field(
        None,
        description="The top-p parameter for nucleus sampling (default is 1.0)",
    )
    n: Optional[int] = Field(
        None,
        description="The number of completions to generate (default is 1)",
    )
    max_tokens: Optional[int] = Field(
        None,
        description="The maximum number of tokens in the \
            generated completion (default is infinity)",
    )
    presence_penalty: Optional[float] = Field(
        None,
        description="It is used to penalize new tokens based on \
            their existence in the text so far.",
    )
    frequency_penalty: Optional[float] = Field(
        None,
        description="It is used to penalize new tokens based on \
            their frequency in the text so far.",
    )
    base_url: Optional[str] = Field(
        None,
        description="Base URL for the API",
    )
    api_version: Optional[str] = Field(
        None,
        description="API version",
    )
    api_key: Optional[str] = Field(
        None,
        description="API key for the API",
    )
    custom_llm_provider: Optional[str] = Field(None, description="Custom LLM provider")

    # litellm class
    timeout: Optional[float] = Field(
        600,
        description="Timeout for the request",
    )
    max_retries: Optional[int] = Field(
        3,
        description="Maximum number of retries",
    )
    default_headers: Optional[dict] = Field(
        None,
        description="Default headers for the request",
    )

    def to_dict(self):
        return self.model_dump()
