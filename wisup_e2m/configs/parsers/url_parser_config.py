from wisup_e2m.configs.parsers.base import BaseParserConfig
from typing import Optional
from pydantic import Field


class UrlParserConfig(BaseParserConfig):

    api_key: Optional[str] = Field(None, description="API key for FireCrawl / fastCRW API")
    api_url: Optional[str] = Field(
        None,
        description="Base URL for the fastCRW (crw) engine. Defaults to the managed "
        "cloud (https://fastcrw.com/api); set to a self-hosted server to override.",
    )
