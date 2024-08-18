import json
import logging
import subprocess
import os
from pathlib import Path
from typing import Dict


logger = logging.getLogger(__name__)
pwd = Path(__file__).parent

"""
- Resource wordnet not found.
  - Download [corpora/wordnet.zip](https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip) manually and unzip it to the directory specified in the error message. Otherwise, you can download it using the following commands:
    - Windows: `wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip -O ~\\AppData\\Roaming\nltk_data\\corpora\\wordnet.zip` and `unzip ~\\AppData\\Roaming\nltk_data\\corpora\\wordnet.zip -d ~\\AppData\\Roaming\nltk_data\\corpora\\`
    - Unix: `wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip -O ~/nltk_data/corpora/wordnet.zip` and `unzip ~/nltk_data/corpora/wordnet.zip -d ~/nltk_data/corpora/`

"""


def check_nltk_corpora_wordnet():
    if os.name == "nt":
        nltk_data_path = os.path.join(os.environ["APPDATA"], "nltk_data")
    else:
        nltk_data_path = os.path.join(os.environ["HOME"], ".nltk_data")
    wordnet_path = os.path.join(nltk_data_path, "corpora", "wordnet")
    if not os.path.exists(wordnet_path):
        import httpx

        with httpx.stream(
            "GET",
            "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip",
        ) as r:
            with open(os.path.join(nltk_data_path, "corpora", "wordnet.zip"), "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        import zipfile

        with zipfile.ZipFile(
            os.path.join(nltk_data_path, "corpora", "wordnet.zip"), "r"
        ) as zip_ref:
            zip_ref.extractall(os.path.join(nltk_data_path, "corpora"))
    return True


def surya_detect_layout(
    input_path, image_limit: int = 100, batch_size: int = 6, max_pages=None
) -> Dict:
    script_path = pwd / "scripts" / "surya_detect_layout.py"

    # 调用 surya_detect_layout.py 脚本作为单独的进程
    logger.info(f"Running script {script_path} to detect layout")
    cmd = [
        "python",
        str(script_path.resolve()),
        str(input_path),
    ]

    if image_limit:
        cmd.extend(["--image_limit", str(image_limit)])

    if batch_size:
        cmd.extend(["--batch_size", str(batch_size)])

    if max_pages:
        cmd.extend(["--max", str(max_pages)])

    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logger.error(f"Error during layout detection: {stderr.decode()}")
            raise RuntimeError(f"Layout detection failed: {stderr.decode()}")
        else:
            logger.info("Layout detection completed successfully.")

    # 确保输出日志中包含调试信息
    logger.debug(f"stdout: {stdout.decode()}")
    logger.debug(f"stderr: {stderr.decode()}")

    # 解析返回的 JSON 结果
    try:
        result = json.loads(stdout.decode())  # list
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {str(e)}")
        raise RuntimeError("Failed to parse JSON output.")

    logger.info(f"Layout detected: {result}")
    return result


def convert_pdf_to_images(file, start_page, end_page, proc_count, save_dir, dpi=200):
    # pdf_to_image_script.py
    script_path = pwd / "scripts" / "pdf_to_images.py"

    # 调用 pdf_converter.py 脚本作为单独的进程
    logger.info(f"Running script {script_path} to convert PDF to images")

    # 可选参数根据用户需求传递
    cmd = ["python", str(script_path.resolve()), str(file), str(save_dir)]

    if start_page:
        cmd.extend(["--start_page", str(start_page)])

    if end_page:
        cmd.extend(["--end_page", str(end_page)])

    if dpi:
        cmd.extend(["--dpi", str(dpi)])

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"PDF conversion failed: {stderr.decode()}")

    logger.info(f"PDF converted to images: {stdout.decode()}")
    # 解析返回的 JSON 结果
    return json.loads(stdout.decode())
