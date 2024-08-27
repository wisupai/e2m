import base64
from mimetypes import guess_type
import io
from typing import IO, Tuple, Union

from PIL import Image

# RGB
WHITE_RGB = (255, 255, 255)
BLUE_RGB = (0, 0, 255)
RED_RGB = (255, 0, 0)
GREEN_RGB = (0, 255, 0)
YELLOW_RGB = (255, 255, 0)
BLACK_RGB = (0, 0, 0)

# BGR
WHITE_BGR = (255, 255, 255)
BLUE_BGR = (255, 0, 0)
RED_BGR = (0, 0, 255)
GREEN_BGR = (0, 255, 0)
YELLOW_BGR = (0, 255, 255)
BLACK_BGR = (0, 0, 0)


# 检查图像的重叠百分比
def check_overlap_percentage(
    image1: Tuple[int, int, int, int], image2: Tuple[int, int, int, int]
) -> float:
    """
    检查两个图像的重叠百分比。

    x1,y1 ------
    |          |
    |          |
    |          |
    --------x2,y2

    x3,y3 ------
    |          |
    |          |
    |          |
    --------x4,y4

    :param image1: 第一个图像的坐标 (x1, y1, x2, y2)
    :param image2: 第二个图像的坐标 (x3, y3, x4, y4)
    :return: 重叠百分比
    """
    x1, y1, x2, y2 = image1
    x3, y3, x4, y4 = image2

    # 检查图像坐标是否有效
    if x1 > x2 or y1 > y2 or x3 > x4 or y3 > y4:
        raise ValueError("无效的图像坐标，左上角坐标应小于右下角坐标。")

    # 先检查图像是否具有包含关系
    if x1 >= x3 and y1 >= y3 and x2 <= x4 and y2 <= y4:
        return 1.0

    if x3 >= x1 and y3 >= y1 and x4 <= x2 and y4 <= y2:
        return 1.0

    # 计算交集区域的坐标
    x_left = max(x1, x3)
    y_top = max(y1, y3)
    x_right = min(x2, x4)
    y_bottom = min(y2, y4)

    # 计算交集区域的面积
    intersection_area = max(0, x_right - x_left) * max(0, y_bottom - y_top)

    # 如果没有交集区域，重叠百分比为0
    if intersection_area == 0:
        return 0.0

    # 计算两个图像的面积
    area1 = (x2 - x1) * (y2 - y1)
    area2 = (x4 - x3) * (y4 - y3)

    # 计算重叠百分比
    overlap_percentage = intersection_area / (area1 + area2 - intersection_area)

    return overlap_percentage


def merge_images(
    image1: Tuple[int, int, int, int], image2: Tuple[int, int, int, int]
) -> Tuple[int, int, int, int]:
    """
    合并两个图像的坐标。

    x1,y1 ------
    |          |
    |          |
    |          |
    --------x2,y2

    x3,y3 ------
    |          |
    |          |
    |          |
    --------x4,y4

    :param image1: 第一个图像的坐标 (x1, y1, x2, y2)
    :param image2: 第二个图像的坐标 (x3, y3, x4, y4)
    :return: 合并后的图像坐标 (x5, y5, x6, y6)
    """
    x1, y1, x2, y2 = image1
    x3, y3, x4, y4 = image2

    # 计算合并后的图像坐标
    x5 = min(x1, x3)
    y5 = min(y1, y3)
    x6 = max(x2, x4)
    y6 = max(y2, y4)

    return x5, y5, x6, y6


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


def base64_to_image(base64_data: str) -> Image:
    """
    将 base64 编码的字符串转换为 PIL Image 对象。

    :param base64_data: base64 编码的字符串
    :return: PIL Image 对象
    """
    image_data = base64.b64decode(base64_data)
    return Image.open(io.BytesIO(image_data))


def image_to_base64(image_input: str) -> str:
    """
    将图片文件转换为 base64 编码的字符串。


    :param image_input: 图片的文件路径
    :return: base64 编码的字符串
    """
    with open(image_input, "rb") as f:
        base64_data = base64.b64encode(f.read())
        return base64_data.decode("utf-8")


def has_transparent_background(image_input: Union[str, IO[bytes]]) -> bool:
    """
    判断给定的图片是否具有透明背景。

    :param image_input: 图片的文件路径或字节流
    :return: 如果图片具有透明背景，返回 True；否则返回 False
    """
    with Image.open(image_input) as img:
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # check alpha channel
            alpha = img.split()[-1]
            if alpha.getextrema()[0] < 255:
                return True
    return False
