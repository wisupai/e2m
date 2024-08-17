from typing import Any, Dict

from pydantic import BaseModel, Field


class E2MParserConfig(BaseModel):

    parsers: Dict[str, Any] = Field(
        {},
        description="Configuration for parsers",
    )


class E2MConverterConfig(BaseModel):

    converters: Dict[str, Any] = Field(
        {},
        description="Configuration for converters",
    )
