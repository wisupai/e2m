# surya_detect_layout.py
import argparse
import json
import os
import sys

from surya.detection import batch_text_detection
from surya.input.load import load_from_file, load_from_folder
from surya.layout import batch_layout_detection
from surya.model.detection.model import load_model, load_processor
from surya.settings import settings


def main():
    parser = argparse.ArgumentParser(
        description="Detect layout of an input file or folder (PDFs or image)."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to pdf or image file or folder to detect layout in.",
    )
    parser.add_argument(
        "--image_limit",
        type=int,
        help="Maximum number of images to process in the same time.",
        default=100,
    )
    parser.add_argument("--max", type=int, help="Maximum number of pages to process.", default=None)
    parser.add_argument(
        "--batch_size",
        type=int,
        help="Batch size to use for processing images.",
        default=6,
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode.", default=False)
    args = parser.parse_args()

    # Suppress all output except print
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    if not args.debug:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    try:
        model = load_model(checkpoint=settings.LAYOUT_MODEL_CHECKPOINT)
        processor = load_processor(checkpoint=settings.LAYOUT_MODEL_CHECKPOINT)
        det_model = load_model()
        det_processor = load_processor()

        if os.path.isdir(args.input_path):
            images, names = load_from_folder(args.input_path, args.max)  # noqa
        else:
            images, names = load_from_file(args.input_path, args.max)  # noqa

        line_predictions = batch_text_detection(images, det_model, det_processor, args.batch_size)

        layout_predictions = batch_layout_detection(
            images, model, processor, line_predictions, args.batch_size
        )

        predictions_by_page = []

        for _, (pred, name) in enumerate(zip(layout_predictions, names)):
            out_pred = pred.model_dump(exclude=["segmentation_map"])
            out_pred["page"] = len(predictions_by_page) + 1
            out_pred["name"] = name
            predictions_by_page.append(out_pred)

    finally:
        # Restore standard output and error for print
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    # JSON格式输出在控制台
    print(json.dumps(predictions_by_page, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
