from abc import ABC
from typing import Any, Dict, Optional

from transformers.models.layoutxlm.tokenization_layoutxlm_fast import List


class BaseParserConfig(ABC):
    """
    Config for Parsers.
    """

    def __init__(
        self,
        engine: str = "unstructured", # unstructured, surya_layout, marker
        langs : List[str] = ["en", "zh"], # refer to https://xiaogliu.github.io/2019/10/11/i18n-locale-code/
    ):
        """
        Initializes a configuration class instance for the Parsers.

        :param engine: Parser engine to use, options are ["unstructured", "surya_layout", "marker"], defaults to unstructured
        :type engine: Optional[str], optional
        :param langs: Languages to use for parsing, defaults to ["en", "zh"]
        :type langs: List[str], optional
        """

        self.engine = engine
        self.langs = langs

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.

        :return: A dictionary containing the configuration
        :rtype: Dict[str, Any]
        """
        return {
            "engine": self.engine,
            "langs": self.langs,
        }
