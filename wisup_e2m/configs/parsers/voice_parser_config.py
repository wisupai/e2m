from typing import Optional

from pydantic import Field, ValidationInfo, field_validator

from wisup_e2m.configs.parsers.base import BaseParserConfig


class VoiceParserConfig(BaseParserConfig):
    # openai whisper settings
    model: Optional[str] = Field(None, description="OpenAI Whisper model to use")

    api_key: Optional[str] = Field(None, description="OpenAI API key to use for Whisper")

    api_base: Optional[str] = Field(None, description="OpenAI API base to use for Whisper")

    @field_validator("model")
    def validate_model(cls, v, values: ValidationInfo):
        # 如果engine是openai_whisper才检查,确保 model 在 whisper.available_models() 中
        if values.data.get("engine") == "openai_whisper":
            try:
                import whisper
            except ImportError:
                raise ImportError(
                    "Whisper not installed. Please install Whisper by `pip install git+https://github.com/openai/whisper.git`"
                ) from None

            available_models = whisper.available_models()
            if v not in available_models:
                raise ValueError(f"model {v} not in {available_models}")
        return v
