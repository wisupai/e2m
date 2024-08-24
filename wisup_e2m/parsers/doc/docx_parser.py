# /e2m/parsers/doc/docx_parser.py
import logging
from typing import Optional
import re
import shutil
from pathlib import Path
import zipfile

from wisup_e2m.configs.parsers.base import BaseParserConfig
from wisup_e2m.parsers.base import BaseParser, E2MParsedData
from wisup_e2m.utils.image_util import has_transparent_background


logger = logging.getLogger(__name__)


_docx_parser_params = [
    "file_name",
    "extract_images",
    "include_image_link_in_text",
    "ignore_transparent_images",
    "work_dir",
    "image_dir",
    "relative_path",
]


class DocxParser(BaseParser):
    SUPPORTED_ENGINES = ["xml"]
    SUPPERTED_FILE_TYPES = ["docx"]

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
        super().__init__(config, **config_kwargs)

        if not self.config.engine:
            self.config.engine = "xml"  # xml
            logger.info(
                f"No engine specified. Defaulting to {self.config.engine} engine."
            )

        self._ensure_engine_exists()
        self._load_engine()

    def _parse_by_xml(
        self,
        file_name: str,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ) -> E2MParsedData:

        from docx import Document
        from uuid import uuid4
        import xml.etree.ElementTree as ET
        from dataclasses import dataclass

        @dataclass
        class DocImage:
            id: str
            target: str | Path
            type: str

            def __str__(self):
                return f"{self.id} : {self.target}"

        image_list = []
        docx_path = Path(file_name)

        # 提取图片
        if extract_images:
            logger.info(f"Extracting images from docx file {docx_path}")
            try:
                tmp_dir = Path(f"./.tmp/docx_unpack_{uuid4()}")
                tmp_dir.mkdir(parents=True, exist_ok=True)
                zip_path = tmp_dir / f"{docx_path.stem}.zip"

                # rename to test2.zip and unzip
                shutil.copy(docx_path, zip_path)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)

                word_dir = tmp_dir / "word"
                rels_xml = tmp_dir / "word/_rels/document.xml.rels"

                with open(rels_xml, "r", encoding="utf-8") as f:
                    rels = f.read()

                rels_xml_tree = ET.fromstring(rels)
                for rel in rels_xml_tree:
                    # 通过 re 找到 type，格式如同 http://schemas.openxmlformats.org/officeDocument/\d+/relationships/image
                    type = rel.get("Type")

                    if not re.match(
                        r"http://schemas.openxmlformats.org/officeDocument/\d+/relationships/image",
                        type,
                    ):
                        continue

                    # 通过 re 找到 id
                    id = rel.get("Id")
                    # 通过 re 找到 target
                    target = rel.get("Target")
                    # 处理 target，如果以 / 开头，则认为是相对路径，需要加上 tmp_dir
                    if target.startswith("/"):
                        target = target[1:]
                    # tmp_dir / target 或者 word_dir / target
                    # 查看哪个存在
                    tmp_target = tmp_dir / target
                    if not tmp_target.exists():
                        tmp_target = word_dir / target

                    logger.info(f"{tmp_target=}")

                    if ignore_transparent_images and has_transparent_background(
                        tmp_target
                    ):
                        logger.info(f"Ignore transparent image {tmp_target}")
                        continue

                    # cp to target_image_dir
                    target_image_dir = Path(image_dir)
                    logger.info(f"Copying {tmp_target} to {target_image_dir}")
                    target_image_dir.mkdir(parents=True, exist_ok=True)

                    target_image_path = target_image_dir / tmp_target.name

                    shutil.copy(tmp_target, target_image_path)

                    # 如果 type 的格式满足 http://schemas.openxmlformats.org/officeDocument/数字/relationships/image

                    image_list.append(
                        DocImage(id=id, target=target_image_path, type=type)
                    )

            except Exception as e:
                logger.error(f"Error extracting images from docx file: {e}")

            finally:
                # remove tmp_dir
                shutil.rmtree(tmp_dir)

        logger.info(f"Found {len(image_list)} images in docx file {docx_path}")

        doc = Document(docx_path)

        text_list = []
        attached_images = []

        for ele in doc.element.body:
            xml = ele.xml
            if ele.text:
                text_list.append(ele.text)

            if include_image_link_in_text:
                if "<w:drawing>" in xml:
                    # <a:blip r:embed="rId8"> or <a:blip r:embed="R7aeea335d84042e6">
                    img_ids = re.findall(r'r:embed="([^"]+)"', xml)

                    for img_id in img_ids:
                        for img in image_list:
                            if img.id == img_id:
                                if relative_path:
                                    text_list.append(
                                        f"![{img.target.name}]({img.target.relative_to(Path(work_dir))})"
                                    )
                                    attached_images.append(str(img.target.relative_to(Path(work_dir))))
                                else:
                                    text_list.append(
                                        f"![{img.target.name}]({img.target})"
                                    )
                                    attached_images.append(str(img.target.resolve()))
                                    logger.info(f"Inserted image {img.target} in text")

        return E2MParsedData(
            text="\n".join(text_list),
            attached_images=attached_images,
            metadata={
                "engine": "xml",
            },
        )

    def get_parsed_data(
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
        """
        Parse the data and return the parsed data

        """
        if file_name:
            DocxParser._validate_input_flie(file_name)

        if self.config.engine == "xml":
            return self._parse_by_xml(
                file_name=file_name,
                extract_images=extract_images,
                include_image_link_in_text=include_image_link_in_text,
                ignore_transparent_images=ignore_transparent_images,
                work_dir=work_dir,
                image_dir=image_dir,
                relative_path=relative_path,
            )
        else:
            raise NotImplementedError(f"Engine {self.config.engine} not supported")

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
            if k in _docx_parser_params:
                kwargs[k] = v

        return self.get_parsed_data(**kwargs)
