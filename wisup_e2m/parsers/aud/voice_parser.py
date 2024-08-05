# /e2m/parsers/aud/voice_parser.py
import logging
from typing import Optional

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData


logger = logging.getLogger(__name__)


class VoiceParser(BaseParser):
    SUPPORTED_ENGINES = ["openai-whisper", "SpeechRecognition"]
    SUPPERTED_FILE_TYPES = ["mp3", "m4a"]

    def __init__(self, config: Optional[BaseParserConfig] = None):
        super().__init__(config)

        if not self.config.engine:
            self.config.engine = "openai-whisper"
            logger.info("No engine specified. Defaulting to unstructured engine.")

        self._ensure_engine_exists()
        self._load_engine()

    def _parse_by_openai_whisper(
        self,
        file: str,
    ):
        result = self.openai_whisper.transcribe(file)

        return E2MParsedData(
            text=result["text"],
            metadata={"engine": "openai-whisper", "openai-whisper_metadata": result},
        )

    def _parse_by_speech_recognition(
        self,
        file: str,
    ):
        """
        ref: https://github.com/Uberi/speech_recognition
        """
        raise NotImplementedError("SpeechRecognition engine is not implemented yet")

    def get_parsed_data(
        self,
        file_name: str,
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        :param file_name: File to parse
        :type file_name: str
        :return: Parsed data
        :rtype: E2MParsedData
        """

        if self.config.engine == "openai-whisper":
            return self._parse_by_openai_whisper(file_name)
        elif self.config.engine == "SpeechRecognition":
            return self._parse_by_speech_recognition(file_name)
        else:
            raise ValueError(f"Engine {self.config.engine} not supported")
