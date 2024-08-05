from PIL import Image
from typing import Union, IO


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
