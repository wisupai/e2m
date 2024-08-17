from typing import List, Optional

from pydantic import BaseModel, Field


class BaseParserConfig(BaseModel):
    """
    Config for Parsers.
    """

    # parser settings
    engine: str = Field(
        "unstructured",
        description="Parser engine to use, options are ['unstructured', 'surya_layout', 'marker']",
    )
    langs: List[str] = Field(
        ["en", "zh"],
        description="Languages to use for parsing, refer to https://xiaogliu.github.io/2019/10/11/i18n-locale-code/",
    )

    # httpx client settings
    client_timeout: int = Field(30, description="Client timeout")
    client_max_redirects: int = Field(5, description="Client max redirects")
    client_proxy: Optional[str] = Field(None, description="Client proxy")

    class Config:
        extra = "allow"
