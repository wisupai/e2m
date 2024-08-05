from pydantic import Field, field_validator, ValidationInfo
from wisup_e2m.configs.parsers.base import BaseParserConfig
from typing import Optional


class VoiceParserConfig(BaseParserConfig):
    # openai whisper settings
    openai_whisper_model: Optional[str] = Field(
        None, description="OpenAI Whisper model to use"
    )

    @field_validator("openai_whisper_model")
    def validate_openai_whisper_model(cls, v, values: ValidationInfo):
        # 如果engine是openai-whisper才检查,确保 openai_whisper_model 在 whisper.available_models() 中
        if values.data.get("engine") == "openai-whisper":
            try:
                import whisper
            except ImportError:
                raise ImportError(
                    "Whisper not installed. Please install Whisper by `pip install git+https://github.com/openai/whisper.git`"
                ) from None

            available_models = whisper.available_models()
            if v not in available_models:
                raise ValueError(f"openai_whisper_model {v} not in {available_models}")
        return v
