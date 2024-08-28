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
    SUPPORTED_ENGINES = ["xml", "pandoc"]
    SUPPERTED_FILE_TYPES = ["docx"]

    def __init__(self, config: Optional[BaseParserConfig] = None, **config_kwargs):
        """
        :param config: BaseParserConfig

        :param engine: str, the engine to use for conversion, default is xml
        :param langs: List[str], the languages to use for parsing, default is ['en', 'zh']
        :param client_timeout: int, the client timeout, default is 30
        :param client_max_redirects: int, the client max redirects, default is 5
        :param client_proxy: Optional[str], the client proxy, default is None
        """
        super().__init__(config, **config_kwargs)

        if not self.config.engine:
            self.config.engine = "pandoc"  # pandoc, xml
            logger.info(
                f"No engine specified. Defaulting to {self.config.engine} engine."
            )

        self._ensure_engine_exists()
        self._load_engine()

    def _parse_by_pandoc(
        self,
        file_name: str,
        extract_images: bool = True,
        include_image_link_in_text: bool = True,
        ignore_transparent_images: bool = False,
        work_dir: str = "./",
        image_dir: str = "./figures",
        relative_path: bool = True,
    ):
        import pypandoc
        import re
        import html2text

        # Step 1: Convert docx to initial markdown
        result = pypandoc.convert_file(
            file_name,
            "markdown_phpextra",
            extra_args=["--extract-media=" + image_dir],
            verify_format=True
        )

        # Step 2: Convert HTML tables to markdown
        table_pattern = re.compile(r"(<table>.*?</table>)", re.DOTALL)
        for match in table_pattern.finditer(result):
            table_html = match.group(1)
            h = html2text.HTML2Text()
            h.body_width = 0
            table_md = h.handle(table_html)
            result = result.replace(table_html, table_md)
        
        # Step 3: Standardize image format
        image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)\{[^}]*\}")
        result = image_pattern.sub(r"![\1](\2)", result)
        
        # Step 4: Remove specific patterns
        to_be_removed_pattern = {
            r"\*\*\s*\n>\s*\*\*": "\n",
            r"\*\*\s*>\s*\*\*": "",
            r">\s*\n": "\n",
        }
        for pattern, replacement in to_be_removed_pattern.items():
            result = re.sub(pattern, replacement, result, flags=re.MULTILINE)
        
        # Step 5: Ensure images are surrounded by empty lines
        image_pattern = re.compile(r'(!\[.*?\]\(.*?\))')
        result = re.sub(image_pattern, r'\n\n\1\n\n', result)
        
        # Step 6: Clean up excessive newlines
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r'\n\s*\n', '\n\n', result)
        
        # Step 7: Strip whitespace from line beginnings and endings
        result = '\n'.join(line.strip() for line in result.split('\n'))


        attached_images = []
        image_folder_path = Path(image_dir) / "media"
        for image_file in image_folder_path.glob('*'):
            if image_file.is_file():
                attached_images.append(str(image_file))
        
        return E2MParsedData(
            text=result,
            attached_images=attached_images,
            metadata={
                "engine": "pandoc",
            },
        )
        


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
            # test >
            print(f"{ele.tag=} | {ele.text=}")
            # test <
            if ele.tag.endswith("bookmarkEnd"):
                text_list.append("\n")
                continue

            if ele.tag.endswith("tbl"):
                self._process_table(ele, text_list)
                text_list.append("\n")
                continue

            if ele.tag.endswith("p"):
                if not ele.text:
                    text_list.append("\n")
                    continue
                if ele.text:
                    if "<w:numPr>" in ele.xml:
                        text_list.append("- " + ele.text)
                    else:
                        text_list.append(ele.text)

                if include_image_link_in_text:
                    self._process_images(
                        ele,
                        image_list,
                        text_list,
                        attached_images,
                        relative_path,
                        work_dir,
                    )

                text_list.append("\n")

                continue

        return E2MParsedData(
            text="\n".join(text_list),
            attached_images=attached_images,
            metadata={
                "engine": "xml",
            },
        )

    def _process_table(self, ele, text_list):
        """
        Process Docx Table to markdown table
        """
        for idx, tr in enumerate(ele.tr_lst):
            row_cells = [self._get_cell_text(tc) for tc in tr.tc_lst]
            text_list.append("|" + " | ".join(row_cells) + "|")
            if idx == 0:
                text_list.append("|" + " | ".join(["---"] * len(row_cells)) + "|")

    def _get_cell_text(self, tc):
        """
        Get the text of the cell
        """
        return "".join(
            "".join(t.text for t in r.t_lst) for p in tc.p_lst for r in p.r_lst
        )

    def _process_images(
        self, ele, image_list, text_list, attached_images, relative_path, work_dir
    ):
        """
        Process the images in the element
        """
        xml = ele.xml
        if "<w:drawing>" in xml:
            img_ids = re.findall(r'r:embed="([^"]+)"', xml)
            for img_id in img_ids:
                for img in image_list:
                    if img.id == img_id:
                        self._add_image_to_text(
                            img, text_list, attached_images, relative_path, work_dir
                        )

    def _add_image_to_text(
        self, img, text_list, attached_images, relative_path, work_dir
    ):
        """
        Add the image to the text
        """
        if relative_path:
            rel_path = img.target.relative_to(Path(work_dir))
            text_list.append(f"![{img.target.name}]({rel_path})")
            attached_images.append(str(rel_path))
        else:
            text_list.append(f"![{img.target.name}]({img.target})")
            attached_images.append(str(img.target.resolve()))
            logger.info(f"Inserted image {img.target} in text")

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
        elif self.config.engine == "pandoc":
            return self._parse_by_pandoc(
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
