# /e2m/parsers/doc_parser.py
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from wisup_e2m.parsers.base import E2MParsedData
from wisup_e2m.parsers.doc.pptx_parser import PptxParser
from wisup_e2m.utils.ppt_util import convert_ppt_to_pptx

logger = logging.getLogger(__name__)

_ppt_parser_params = [
    "file_name",
    "start_page",
    "end_page",
    "include_page_breaks",
    "include_slide_notes",
    "infer_table_structure",
    "extract_images",
    "include_image_link_in_text",
    "ignore_transparent_images",
    "work_dir",
    "image_dir",
    "relative_path",
]


class PptParser(PptxParser):
    SUPPERTED_FILE_TYPES = ["ppt"]

    def get_parsed_data(
        self,
        file_name: str = None,
        start_page: int = None,
        end_page: int = None,
        include_page_breaks: bool = True,
        include_slide_notes: Optional[bool] = None,
        infer_table_structure: bool = True,
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
        PptParser._validate_input_flie(file_name)

        try:
            tmp_dir = Path(f"./.tmp/{uuid4()}")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_file_name = tmp_dir / f"{uuid4()}.pptx"
            convert_ppt_to_pptx(file_name, str(tmp_file_name))
            file_name = str(tmp_file_name)

            for k, v in locals().items():
                if k in _ppt_parser_params:
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
        file_name: str = None,
        start_page: int = None,
        end_page: int = None,
        include_page_breaks: bool = True,
        include_slide_notes: Optional[bool] = None,
        infer_table_structure: bool = True,
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
            if k in _ppt_parser_params:
                kwargs[k] = v

        return self.get_parsed_data(**kwargs)
