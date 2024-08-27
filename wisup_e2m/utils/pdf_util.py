import json
import logging
import subprocess
import os
from pathlib import Path
import httpx
import zipfile
from typing import Dict, List


logger = logging.getLogger(__name__)
pwd = Path(__file__).parent

"""
- Resource wordnet not found.
  - Download [corpora/wordnet.zip](https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip) manually and unzip it to the directory specified in the error message. Otherwise, you can download it using the following commands:
    - Windows: `wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip -O ~\\AppData\\Roaming\nltk_data\\corpora\\wordnet.zip` and `unzip ~\\AppData\\Roaming\nltk_data\\corpora\\wordnet.zip -d ~\\AppData\\Roaming\nltk_data\\corpora\\`
    - Unix: `wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip -O ~/nltk_data/corpora/wordnet.zip` and `unzip ~/nltk_data/corpora/wordnet.zip -d ~/nltk_data/corpora/`

"""


def check_nltk_corpora_wordnet():
    # 确定操作系统并设置NLTK数据路径
    if os.name == "nt":
        nltk_data_path = os.path.join(os.environ["APPDATA"], "nltk_data")
    else:
        nltk_data_path = os.path.join(os.environ["HOME"], "nltk_data")

    # 构建WordNet目录和zip文件的路径
    corpara_dir_path = os.path.join(nltk_data_path, "corpora")
    wordnet_dir_path = os.path.join(nltk_data_path, "corpora", "wordnet")
    wordnet_zip_path = os.path.join(nltk_data_path, "corpora", "wordnet.zip")

    # 检查corpora目录是否存在，如果不存在则创建
    if not os.path.exists(corpara_dir_path):
        os.makedirs(corpara_dir_path)
        print(f"Creating the directory {corpara_dir_path}")

    # 检查wordnet.zip是否存在，如果不存在则下载
    if not os.path.exists(wordnet_dir_path):
        url = (
            "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip"
        )
        print(f"The WordNet corpus is not installed. Starting to download from {url}")

        try:
            # 使用httpx发送GET请求
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()  # 确保请求成功

                # 写入zip文件
                with open(wordnet_zip_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
        except httpx.RequestError as e:
            print(f"An error occurred while downloading: {e}")
            return False

        # 解压wordnet.zip到指定目录
        try:
            with zipfile.ZipFile(wordnet_zip_path, "r") as zip_ref:
                zip_ref.extractall(corpara_dir_path)
                print(f"WordNet corpus downloaded and extracted to {corpara_dir_path}")

        except zipfile.BadZipFile as e:
            print(f"An error occurred while extracting: {e}")
            return False
        except Exception as e:
            print(f"An unknown error occurred: {e}")
            return False

        # 下载并解压完成后，删除zip文件
        os.remove(wordnet_zip_path)
    else:
        print("WordNet corpus is already installed.")

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


def marker_convert_single(
    filename: str,
    start_page: int = None,
    max_pages: int = None,
    langs: List[str] = None,
    batch_multiplier: int = 2,
    debug: bool = False,
) -> None:
    script_path = Path(__file__).parent / "scripts" / "marker_convert_single.py"

    logger.info(f"Running script {script_path} to convert PDF to markdown")

    # 构建命令行参数
    cmd = ["python", str(script_path.resolve()), filename]

    if start_page is not None:
        cmd.extend(["--start_page", str(start_page)])

    if max_pages is not None:
        cmd.extend(["--max_pages", str(max_pages)])

    if langs:
        # 将列表转换为逗号分隔的字符串
        lang_str = ",".join(langs)
        cmd.extend(["--langs", lang_str])

    if batch_multiplier:
        cmd.extend(["--batch_multiplier", str(batch_multiplier)])

    if debug:
        cmd.append("--debug")

    print("Start running marker, it may take several minutes, please wait...")

    # 运行脚本
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        logger.error(f"Error during PDF conversion: {stderr.decode()}")
        raise RuntimeError(f"PDF conversion failed: {stderr.decode()}")
    else:
        logger.info("PDF conversion completed successfully.")

    logger.debug(f"stdout: {stdout.decode()}")
    logger.debug(f"stderr: {stderr.decode()}")

    # 解析返回的 JSON 结果
    try:
        result = json.loads(stdout.decode())  # list
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {str(e)}")
        raise RuntimeError(f"Failed to parse JSON output, stdout.decode() = {stdout.decode()}")

    logger.info(f"PDF converted to markdown: {result}")
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


if __name__ == "__main__":
    # check_nltk_corpora_wordnet
    check_nltk_corpora_wordnet()
