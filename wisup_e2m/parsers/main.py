import logging
from typing import Any, Dict, Optional, Union

from pydantic import ValidationError

from wisup_e2m.configs.base import E2MParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.factory import ParserFactory

logger = logging.getLogger(__name__)

parser_default_config = {
    "doc_parser": {
        "engine": "unstructured",
        "langs": ["en", "zh"],
    },
    "docx_parser": {
        "engine": "unstructured",
        "langs": ["en", "zh"],
    },
    "epub_parser": {
        "engine": "unstructured",
        "langs": ["en", "zh"],
    },
    "html_parser": {
        "engine": "unstructured",
        "langs": ["en", "zh"],
    },
    "url_parser": {
        "engine": "jina",
        "langs": ["en", "zh"],
    },
    "pdf_parser": {
        "engine": "marker",
        "langs": ["en", "zh"],
    },
    "ppt_parser": {
        "engine": "unstructured",
        "langs": ["en", "zh"],
    },
    "pptx_parser": {
        "engine": "unstructured",
        "langs": ["en", "zh"],
    },
    "voice_parser": {
        "engine": "openai_whisper_local",
        "model": "large",  # # available models: https://github.com/openai/whisper#available-models-and-languages
    },
}


class E2MParser:
    """
    Parse everything to text and images
    """

    def __init__(self, config: E2MParserConfig = None):
        logger.info("Initializing E2MParser...")
        if not config:
            config = E2MParserConfig(parsers=parser_default_config)
            logger.info("Using default configuration.")
        self.config = config
        self.file_type_to_parser_map: Dict[str, BaseParser] = {}

        for parser_name, parser_config in self.config.parsers.items():
            print(f"Initializing parser: {parser_name}")
            this_parser = ParserFactory.create(parser_name, parser_config)
            setattr(self, parser_name, this_parser)
            # set up the mapping of file types to parsers
            for file_type in this_parser.SUPPERTED_FILE_TYPES:
                self.file_type_to_parser_map[file_type] = this_parser

        print(
            f"E2MParser initialized successfully, including parsers: {list(self.config.parsers.keys())}, able to parse file types: {list(self.file_type_to_parser_map.keys())}"
        )

    @classmethod
    def from_config(cls, config_dict: Union[Dict[str, Any] | str] = "./config.yaml"):
        if isinstance(config_dict, str):
            if not (config_dict.endswith(".yaml") or config_dict.endswith(".yml")):
                raise ValueError("Only yaml files are supported.")
            import yaml

            with open(config_dict, "r") as f:
                config_dict = yaml.safe_load(f)

        try:
            logger.info("Loading configuration...")
            config = E2MParserConfig(**config_dict)
            logger.info("Configuration loaded successfully.")
        except ValidationError as e:
            logging.error(f"Configuration validation error: {e}")
            raise
        return cls(config)

    def parse(
        self,
        file_name: str = None,
        url: str = None,
        start_page: int = None,
        end_page: int = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> Optional[E2MParsedData]:
        """
        Parse the data using the appropriate parser
        """
        if not file_name and not url:
            raise ValueError("Either file_name or url must be provided.")
        if file_name and url:
            raise ValueError("Only one of file_name or url should be provided.")

        file_type = "url" if url else file_name.split(".")[-1].lower()
        parser = self.file_type_to_parser_map.get(file_type)
        if not parser:
            raise ValueError(
                f"Unsupported file type: {file_type}, only {self.file_type_to_parser_map.keys()} are supported.\
                You can add more parsers to the configuration."
            )

        try:
            data = parser.get_parsed_data(
                file_name=file_name,
                url=url,
                start_page=start_page,
                end_page=end_page,
                extract_images=extract_images,
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
                **kwargs,
            )
            return data
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            return None
