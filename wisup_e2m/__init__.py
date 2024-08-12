import importlib.metadata

__version__ = importlib.metadata.version("wisup_e2m")

# doc parser
from wisup_e2m.parsers.doc.pdf_parser import PdfParser  # noqa
from wisup_e2m.parsers.doc.html_parser import HtmlParser  # noqa
from wisup_e2m.parsers.doc.pptx_parser import PptxParser  # noqa
from wisup_e2m.parsers.doc.epub_parser import EpubParser  # noqa
from wisup_e2m.parsers.doc.docx_parser import DocxParser  # noqa
from wisup_e2m.parsers.doc.doc_parser import DocParser  # noqa
from wisup_e2m.parsers.doc.url_parser import UrlParser  # noqa

# aud parser
from wisup_e2m.parsers.aud.voice_parser import VoiceParser  # noqa

# main
from wisup_e2m.parsers.main import E2MParser  # noqa

# converter
from wisup_e2m.converters.text_converter import TextConverter  # noqa
from wisup_e2m.converters.image_converter import ImageConverter  # noqa
