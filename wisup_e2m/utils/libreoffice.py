import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def check_libo_installed():
    """Check if LibreOffice is installed on the system."""
    try:
        subprocess.run(
            ["soffice", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except FileNotFoundError:
        return False


def suggest_libo_installation():
    """Suggest installation commands for LibreOffice based on the operating system."""
    if sys.platform.startswith("linux"):
        return "sudo apt-get install libreoffice"
    elif sys.platform == "darwin":
        return "brew install --cask libreoffice"
    elif sys.platform == "win32":
        return "Please download and install LibreOffice from https://www.libreoffice.org/"
    else:
        return "Unknown system. Please install LibreOffice manually."


def convert_by_libreoffice(
    input_path: str,
    output_format: str,
    output_path: str = None,
    rm_original: bool = False,
):
    """Convert a file to a specified format using LibreOffice.

    Args:
        input_path: The path to the input file.
        output_format: The desired output format (e.g., "docx", "pptx", "pdf").
        output_path: The path to the output file. If None, the output will be in the same directory as the input file.
        rm_original: Whether to remove the original input file after conversion.

    Raises:
        subprocess.CalledProcessError: If the conversion command fails.
        FileNotFoundError: If LibreOffice is not installed.

    """

    if not check_libo_installed():
        installation_command = suggest_libo_installation()
        logger.error(
            f"LibreOffice is not installed. Please install it using the following command: {installation_command}"
        )
        raise FileNotFoundError("LibreOffice is not installed.")

    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(input_path),
            os.path.splitext(os.path.basename(input_path))[0] + f".{output_format}",
        )

    output_dir = os.path.dirname(output_path)

    logger.info(f"Converting [{input_path}] to [{output_path}] with format [{output_format}]")

    # Construct the command to convert the file using LibreOffice
    command = [
        "soffice",
        "--headless",
        "--convert-to",
        output_format,
        input_path,
        "--outdir",
        output_dir,
    ]

    # Execute the command
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Rename the converted file to the desired output filename if necessary
    converted_file = os.path.join(
        output_dir,
        Path(input_path).stem + f".{output_format}",
    )

    if converted_file != output_path:
        os.rename(converted_file, output_path)

    # Remove the original input file if specified
    if rm_original:
        os.remove(input_path)

    logger.info(f"Conversion completed: {output_path}")
