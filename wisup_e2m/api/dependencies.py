from functools import lru_cache
from wisup_e2m import E2MParser, E2MConverter
import yaml
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class InstancePool:
    _parser_instances: Dict[str, E2MParser] = {}
    _converter_instances: Dict[str, E2MConverter] = {}

    @classmethod
    def get_parser(cls, config: Dict[str, Any]) -> E2MParser:
        config_str = yaml.dump(config, sort_keys=True)
        if config_str not in cls._parser_instances:
            logger.info(f"Creating new E2MParser instance with config: {config}")
            cls._parser_instances[config_str] = E2MParser.from_config(config)
        logger.info("Parse found")
        return cls._parser_instances[config_str]

    @classmethod
    def get_converter(cls, config: Dict[str, Any]) -> E2MConverter:
        config_str = yaml.dump(config, sort_keys=True)
        if config_str not in cls._converter_instances:
            logger.info(f"Creating new E2MConverter instance with config: {config}")
            cls._converter_instances[config_str] = E2MConverter.from_config(config)
        logger.info("Converter found")
        return cls._converter_instances[config_str]


@lru_cache()
def load_config() -> Dict[str, Any]:
    config_path = "config.yaml"  # 硬编码配置文件路径
    logger.info(f"Loading configuration from {config_path}")
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        logger.info(f"Configuration loaded successfully: {config}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise


@lru_cache()
def get_parser() -> E2MParser:
    config = load_config()
    parser_config = config.get("parsers", {})
    logger.info(f"{parser_config=}")
    if not parser_config:
        logger.warning("No parser configuration found in the config file")
    return InstancePool.get_parser({"parsers": parser_config})


@lru_cache()
def get_converter() -> E2MConverter:
    config = load_config()
    converter_config = config.get("converters", {})
    logger.info(f"{converter_config=}")
    if not converter_config:
        logger.warning("No converter configuration found in the config file")
    return InstancePool.get_converter({"converters": converter_config})
