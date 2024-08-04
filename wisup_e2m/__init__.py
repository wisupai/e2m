import importlib.metadata

__version__ = importlib.metadata.version("e2m")

from e2m.parsers.doc.pdf_parser import PdfParser  # noqa
