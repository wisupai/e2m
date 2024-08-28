import io
import os
from typing import IO, Any, Dict, Union

from docx import Document

from wisup_e2m.utils.image_util import has_transparent_background


def get_docx_images(
    file_name: Union[str, None],
    file: Union[IO[bytes], None],
    target_image_dir: str,
    ignore_transparent_images: bool = False,
) -> Dict[int, Any]:
    os.makedirs(target_image_dir, exist_ok=True)
    image_dict = {}

    if file_name:
        doc = Document(file_name)
    elif file:
        file_content = io.BytesIO(file.read())
        doc = Document(file_content)
    else:
        raise ValueError("Either file_name or file must be provided")

    image_count = 0

    for idx, rel in enumerate(doc.part.rels.values()):
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob

            if ignore_transparent_images and has_transparent_background(io.BytesIO(image_bytes)):
                continue

            image_ext = rel.target_part.content_type.split("/")[-1]
            image_name = f"{idx}_{image_count}.{image_ext}"
            image_file = os.path.join(target_image_dir, image_name)
            with open(image_file, "wb") as f:
                f.write(image_bytes)

            if idx not in image_dict:
                image_dict[idx] = []

            image_dict[idx].append(
                {
                    "image_number": idx,
                    "image_file": image_file,
                    "image_name": image_name,
                }
            )
            image_count += 1

    return image_dict  # {image_number: [{'image_number': 0, 'image_file': 'extracted_images/0_0.png', 'image_name': '0_0.png'}]}