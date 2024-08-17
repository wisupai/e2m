# pdf_to_image_script.py
import argparse
import json
from pathlib import Path

from pdf2image import convert_from_path


def convert_pdf_to_images(pdf_path, output_dir, start_page, end_page, dpi=200):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = convert_from_path(
        pdf_path,
        first_page=start_page,
        last_page=end_page,
        dpi=dpi,
        output_folder=str(output_dir),
        fmt="png",
        paths_only=True,
    )

    return sorted(images)


if __name__ == "__main__":
    # 从命令行参数获取输入
    parser = argparse.ArgumentParser(description="Convert a PDF file to images.")

    parser.add_argument("pdf_path", type=str, help="Path to the PDF file.")

    parser.add_argument("output_dir", type=str, help="Path to the output directory.")

    parser.add_argument(
        "--start_page",
        type=int,
        help="The page number to start converting from.",
        default=0,
    )

    parser.add_argument(
        "--end_page",
        type=int,
        help="The page number to stop converting at.",
        default=None,
    )

    parser.add_argument(
        "--dpi",
        type=int,
        help="The DPI to use when converting the PDF to images.",
        default=200,
    )

    args = parser.parse_args()
    pdf_path = args.pdf_path
    output_dir = args.output_dir
    start_page = args.start_page
    end_page = args.end_page
    dpi = args.dpi

    # 执行转换
    image_paths = convert_pdf_to_images(pdf_path, output_dir, start_page, end_page, dpi)

    # 将结果打印到标准输出，主程序将从这里读取结果
    print(json.dumps(image_paths))
