# /e2m/parsers/doc_parser.py
import logging

from typing import Optional, IO

from wisup_e2m.parsers.base import E2MParsedData
from wisup_e2m.parsers.doc.docx_parser import DocxParser
from wisup_e2m.utils.doc_util import convert_doc_to_docx


logger = logging.getLogger(__name__)

_doc_parser_params = [
    "file_name",
    "file",
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
        ignore_transparent_images: bool = True,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
        **kwargs,
    ) -> E2MParsedData:
        """
        Parse the data and return the parsed data

        """
        if not file_name:
            raise ValueError("file_name is required")

        if file_name.endswith(".doc"):
            docx_file = file_name.replace(".doc", ".docx")
            convert_doc_to_docx(file_name, docx_file)
            file_name = docx_file

        for k, v in locals().items():
            kwargs[k] = v

        return super().get_parsed_data(**kwargs)

    def parse(
        self,
        file_name: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = True,
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
