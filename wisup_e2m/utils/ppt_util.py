import logging

from wisup_e2m.utils.libreoffice import convert_by_libreoffice

logger = logging.getLogger(__name__)


def convert_ppt_to_pptx(ppt_path: str, pptx_path: str, rm_original: bool = False):
    """Convert a .ppt file to a .pptx file.

    Args:
        ppt_path: The path to the .ppt file.
        pptx_path: The path to the .pptx file.
        rm_original: Whether to remove the original .ppt file after conversion.

    Raises:
        subprocess.CalledProcessError: If the conversion command fails.
        FileNotFoundError: If LibreOffice is not installed.

    """

    convert_by_libreoffice(ppt_path, "pptx", pptx_path, rm_original)
