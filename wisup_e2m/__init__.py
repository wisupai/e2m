import importlib.metadata

__version__ = importlib.metadata.version("e2m")

from wisup_e2m.parsers.doc.pdf_parser import PdfParser  # noqa
