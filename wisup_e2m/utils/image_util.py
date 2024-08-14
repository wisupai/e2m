from PIL import Image
from typing import Union, IO
import base64
from mimetypes import guess_type


# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


def has_transparent_background(image_input: Union[str, IO[bytes]]) -> bool:
    """
    判断给定的图片是否具有透明背景。

    :param image_input: 图片的文件路径或字节流
    :return: 如果图片具有透明背景，返回 True；否则返回 False
    """
    with Image.open(image_input) as img:
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            # 检查alpha通道
            alpha = img.split()[-1]
            if alpha.getextrema()[0] < 255:
                return True
    return False
