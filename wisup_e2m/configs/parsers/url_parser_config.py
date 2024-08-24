from wisup_e2m.configs.parsers.base import BaseParserConfig
from typing import Optional
from pydantic import Field


class UrlParserConfig(BaseParserConfig):

    api_key: Optional[str] = Field(None, description="API key for FireCrawl API")
