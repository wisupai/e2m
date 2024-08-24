# /e2m/parsers/aud/voice_parser.py
import logging
from typing import Optional

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData

logger = logging.getLogger(__name__)


_voice_parser_params = ["file_name"]


class VoiceParser(BaseParser):
    SUPPORTED_ENGINES = [
        "openai_whisper_api",
        "openai_whisper_local",
        "SpeechRecognition",
    ]
    SUPPERTED_FILE_TYPES = ["mp3", "m4a"]

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
        """
        :param config: BaseParserConfig

        :param engine: str, the engine to use for conversion, default is  openai_whisper_local, options are ['openai_whisper_api', 'openai_whisper_local', 'SpeechRecognition']
        :param langs: List[str], the languages to use for parsing, default is ['en', 'zh']
        :param client_timeout: int, the client timeout, default is 30
        :param client_max_redirects: int, the client max redirects, default is 5
        :param client_proxy: Optional[str], the client proxy, default is None
        """
        super().__init__(config, **config_kwargs)

        if not self.config.engine:
            self.config.engine = "openai_whisper_local"
            logger.info(f"No engine specified. Defaulting to {self.config.engine} engine.")

        self._ensure_engine_exists()
        self._load_engine()

    def _parse_by_openai_whisper_local(
        self,
        file: str,
    ):
        result = self.openai_whisper.transcribe(file)

        return E2MParsedData(
            text=result["text"],
            metadata={
                "engine": "openai-whisper",
                "openai_whisper_local_metadata": result,
            },
        )

    def _parse_by_openai_whisper_api(
        self,
        file: str,
    ):

        audio_file = open(file, "rb")

        # check config
        if not self.config.api_key:
            raise ValueError("api_key is required for openai-whisper-api engine")
        if not self.config.api_base:
            raise ValueError("api_base is required for openai-whisper-api engine")
        if not self.config.model:
            raise ValueError("model is required for openai-whisper-api engine")

        response = self.openai_whisper_api_func(
            model=self.config.model,
            file=audio_file,
            api_base=self.config.api_base,
            api_key=self.config.api_key,
            custom_llm_provider="openai",
        )

        return E2MParsedData(
            text=response.text,
            metadata={
                "engine": "openai-whisper",
                "openai_whisper_api_metadata": response.to_dict(),
            },
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

        if file_name:
            VoiceParser._validate_input_flie(file_name)

        if self.config.engine == "openai_whisper_api":
            return self._parse_by_openai_whisper_api(file_name)
        elif self.config.engine == "openai_whisper_local":
            return self._parse_by_openai_whisper_local(file_name)
        elif self.config.engine == "SpeechRecognition":
            return self._parse_by_speech_recognition(file_name)
        else:
            raise ValueError(f"Engine {self.config.engine} not supported")

    def parse(
        self,
        file_name: str,
        **kwargs,
    ):
        for k, v in locals().items():
            if k in _voice_parser_params:
                kwargs[k] = v

        return self.get_parsed_data(**kwargs)
