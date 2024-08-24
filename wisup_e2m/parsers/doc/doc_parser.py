# /e2m/parsers/doc_parser.py
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from wisup_e2m.parsers.base import E2MParsedData
from wisup_e2m.parsers.doc.docx_parser import DocxParser
from wisup_e2m.utils.doc_util import convert_doc_to_docx

logger = logging.getLogger(__name__)

_doc_parser_params = [
    "file_name",
    "extract_images",
    "include_image_link_in_text",
    "ignore_transparent_images",
    "work_dir",
    "image_dir",
    "relative_path",
]


class DocParser(DocxParser):
    SUPPERTED_FILE_TYPES = ["doc"]

    def get_parsed_data(
        self,
        file_name: str,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        """

        DocParser._validate_input_flie(file_name)

        try:
            tmp_dir = Path(f"./.tmp/{uuid4()}")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_file_name = tmp_dir / f"{uuid4()}.docx"
            convert_doc_to_docx(file_name, str(tmp_file_name))
            file_name = str(tmp_file_name)

            for k, v in locals().items():
                if k in _doc_parser_params:
                    kwargs[k] = v

            data = super().get_parsed_data(**kwargs)

            return data

        except Exception as e:
            logger.error(f"Error converting {file_name} to docx: {e}")
            raise
        finally:
            if tmp_file_name.exists():
                tmp_file_name.unlink()

    def parse(
        self,
        file_name: Optional[str] = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """Parse the data and return the parsed data

        :return: Parsed data
        :rtype: E2MParsedData
        """
        for k, v in locals().items():
            if k in _doc_parser_params:
                kwargs[k] = v

        return self.get_parsed_data(**kwargs)
