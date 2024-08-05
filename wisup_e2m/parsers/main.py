import logging
from pydantic import BaseModel, field_validator, ValidationError
from typing import Any, Dict, List, Optional, Union

from wisup_e2m.utils.factory import ParserFactory
from wisup_e2m.configs.base import E2MParserConfig
from wisup_e2m.parsers.base import E2MParsedData, BaseParser

logger = logging.getLogger(__name__)


class E2MParser:
    def __init__(self, config: E2MParserConfig):
        logger.info("Initializing E2MParser...")
        self.config = config
        self.file_type_to_parser_map: Dict[str, BaseParser] = {}

        for parser_name, parser_config in self.config.parsers.items():
            logger.info(f"Initializing parser: {parser_name}")
            this_parser = ParserFactory.create(parser_name, parser_config)
            setattr(self, parser_name, this_parser)
            # set up the mapping of file types to parsers
            for file_type in this_parser.SUPPERTED_FILE_TYPES:
                self.file_type_to_parser_map[file_type] = this_parser

        logger.info(
            f"E2MParser initialized successfully, including parsers: {list(self.config.parsers.keys())}, able to parse file types: {list(self.file_type_to_parser_map.keys())}"
        )

    @classmethod
    def from_config(cls, config_dict: Union[Dict[str, Any] | str]):
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
        include_image_link_in_text: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
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
                include_image_link_in_text=include_image_link_in_text,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
            return data
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            return None