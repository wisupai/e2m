from pydantic import BaseModel, Field
from typing import Optional


class BaseConverterConfig(BaseModel):
    """
    Config for Converters.
    """

    # converter settings
    engine: str = Field(
        "litellm",
        description="Engine to use for conversion (litellm)",
    )

    # liellm completion config
    model: str = Field(
        "deepseek/deepseek-chat",
        description="Model to use for conversion",
    )
    timeout: Optional[float] = Field(
        None,
        description="Timeout for the request",
    )
    temperature: Optional[float] = Field(
        None,
        description="The temperature parameter for controlling the randomness of the output (default is 1.0)",
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
        description="The maximum number of tokens in the generated completion (default is infinity)",
    )
    presence_penalty: Optional[float] = Field(
        None,
        description="It is used to penalize new tokens based on their existence in the text so far.",
    )
    frequency_penalty: Optional[float] = Field(
        None,
        description="It is used to penalize new tokens based on their frequency in the text so far.",
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
