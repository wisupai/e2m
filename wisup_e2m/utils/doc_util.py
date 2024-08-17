import logging

from wisup_e2m.utils.libreoffice import convert_by_libreoffice

logger = logging.getLogger(__name__)


def convert_doc_to_docx(doc_path: str, docx_path: str, rm_original: bool = False):
    """Convert a .doc file to a .docx file.

    Args:
        doc_path: The path to the .doc file.
        docx_path: The path to the .docx file.
        rm_original: Whether to remove the original .doc file after conversion.

    Raises:
        subprocess.CalledProcessError: If the conversion command fails.

    """

    convert_by_libreoffice(doc_path, "docx", docx_path, rm_original)
