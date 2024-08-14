# /e2m/parsers/doc_parser.py
import logging

from wisup_e2m.parsers.base import E2MParsedData
from wisup_e2m.parsers.doc.docx_parser import DocxParser
from wisup_e2m.utils.doc_util import convert_doc_to_docx


logger = logging.getLogger(__name__)


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

        return super().get_parsed_data(
            file_name=file_name,
            extract_images=extract_images,
            include_image_link_in_text=include_image_link_in_text,
            ignore_transparent_images=ignore_transparent_images,
            work_dir=work_dir,
            image_dir=image_dir,
            relative_path=relative_path,
        )
