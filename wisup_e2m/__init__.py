import importlib.metadata

__version__ = importlib.metadata.version("e2m")

# doc parser
from wisup_e2m.parsers.doc.pdf_parser import PdfParser  # noqa
from wisup_e2m.parsers.doc.html_parser import HtmlParser  # noqa
from wisup_e2m.parsers.doc.pptx_parser import PptxParser  # noqa
from wisup_e2m.parsers.doc.epub_parser import EpubParser  # noqa
from wisup_e2m.parsers.doc.docx_parser import DocxParser  # noqa
from wisup_e2m.parsers.doc.doc_parser import DocParser  # noqa

# aud parser
from wisup_e2m.parsers.aud.voice_parser import VoiceParser  # noqa
