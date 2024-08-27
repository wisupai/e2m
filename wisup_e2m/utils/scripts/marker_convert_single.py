import os
import argparse
import json
import base64
from io import BytesIO
import sys

from marker.convert import convert_single_pdf
from marker.logger import configure_logging
from marker.models import load_all_models

# Set environment variable for PyTorch
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

configure_logging()


def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # 将图像保存到内存中，格式为 PNG
    image_bytes = buffered.getvalue()  # 获取字节数据
    return image_bytes


def encode_image_to_base64(image):
    image_bytes = image_to_base64(image)
    base64_str = base64.b64encode(image_bytes).decode("utf-8")  # 编码并解码为字符串
    return base64_str


def main():
    """
    e.g.

    python marker_convert_single.py test.pdf output --start_page 0 --max_pages 1 --langs en --batch_multiplier 1
    """
    parser = argparse.ArgumentParser(description="Convert a PDF to markdown with optional OCR.")
    parser.add_argument("filename", help="PDF file to parse")
    parser.add_argument("--start_page", type=int, default=None, help="Page to start processing at")
    parser.add_argument(
        "--max_pages", type=int, default=None, help="Maximum number of pages to parse"
    )
    parser.add_argument(
        "--langs",
        type=str,
        help="Languages to use for OCR, comma separated",
        default=None,
    )
    parser.add_argument(
        "--batch_multiplier",
        type=int,
        default=2,
        help="How much to increase batch sizes",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging", default=False)
    args = parser.parse_args()

    # Suppress all output except print
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    if not args.debug:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    # Process languages if provided
    langs = args.langs.split(",") if args.langs else None

    # Start processing
    fname = args.filename
    model_lst = load_all_models()

    try:
        # Convert the PDF to markdown and other outputs
        full_text, images, out_meta = convert_single_pdf(
            fname,
            model_lst,
            max_pages=args.max_pages,
            langs=langs,
            batch_multiplier=args.batch_multiplier,
            start_page=args.start_page,
        )

        # print(f"type of images: {type(images)}")
        # print(f"images: {images}") # images: {'0_image_0.png': <PIL.Image.Image image mode=RGB size=128x58 at 0x3F6E4D300>}

        # 把每张image 进行base64编码
        for key, value in images.items():
            images[key] = encode_image_to_base64(value)

        # Prepare the output dictionary with only the required fields
        result = {
            "full_text": full_text,
            "images": images,  # Dict[str, str]
            "out_meta": out_meta,
        }

    except Exception as e:
        # Output error as JSON if an exception occurs
        result = {"error": str(e)}
    finally:
        # Restore stdout and stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    # Output the results as a JSON dictionary
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # save json
    with open(os.path.join("output.json"), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
