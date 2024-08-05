from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import List, Optional


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
    # openai whisper settings
    openai_whisper_model: Optional[str] = Field(
        None, description="OpenAI Whisper model to use"
    )
    # httpx client settings
    client_timeout: int = Field(30, description="Client timeout")
    client_max_redirects: int = Field(5, description="Client max redirects")
    client_proxy: Optional[str] = Field(None, description="Client proxy")

    @field_validator("openai_whisper_model")
    def validate_openai_whisper_model(cls, v, values: ValidationInfo):
        # 如果engine是openai-whisper才检查,确保 openai_whisper_model 在 whisper.available_models() 中
        if values.data.get("engine") == "openai-whisper":
            import whisper

            available_models = whisper.available_models()
            if v not in available_models:
                raise ValueError(f"openai_whisper_model {v} not in {available_models}")
        return v
