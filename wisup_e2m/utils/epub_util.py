import io
import os
from typing import IO, Any, Dict, Union

from ebooklib import epub

from wisup_e2m.utils.image_util import has_transparent_background


def get_epub_images(
    file_name: Union[str, None],
    file: Union[IO[bytes], None],
    target_image_dir: str,
    ignore_transparent_images: bool = False,
) -> Dict[int, Any]:
    os.makedirs(target_image_dir, exist_ok=True)
    image_dict = {}

    if file_name:
        book = epub.read_epub(file_name)
    elif file:
        file_content = file.read()
        book = epub.read_epub(io.BytesIO(file_content))
    else:
        raise ValueError("Either file_name or file must be provided")

    for idx, item in enumerate(book.get_items()):
        if item.media_type.startswith("image/"):
            image_bytes = item.content

            if ignore_transparent_images and has_transparent_background(io.BytesIO(image_bytes)):
                continue

            image_name = f"{idx}_{item.file_name.split('/')[-1]}"
            image_path = os.path.join(target_image_dir, image_name)
            with open(image_path, "wb") as f:
                f.write(image_bytes)

            if idx not in image_dict:
                image_dict[idx] = []

            image_dict[idx].append(
                {
                    "image_file": image_path,
                    "image_name": image_name,
                }
            )

    print(image_dict)

    return image_dict  # {page_number: [{'image_file': 'path/to/image', 'image_name': 'name'}]}
