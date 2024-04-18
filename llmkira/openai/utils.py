from io import BytesIO
from typing import Literal

from PIL import Image


def resize_openai_image(
    image_bytes: bytes, mode: Literal["low", "high", "auto"] = "auto"
) -> bytes:
    """
    如果是 low,缩放到 512*512。如果是 high,图像的短边应小于 768 像素，长边应小于 2,000 像素，如果大于这个尺寸，按比例缩放到这个尺寸，长宽比不变。如果是 Auto，如果尺寸大于512但是小于 768，缩放到 512,如果长边大于2000或宽边大于768,按照比例缩放到合适的尺寸
    https://platform.openai.com/docs/guides/vision
    :param image_bytes: 图片的二进制数据
    :param mode: 模式
    :return: 处理后的图片二进制数据
    """
    # 将 bytes 转换为图片对象
    image = Image.open(BytesIO(image_bytes))
    # 获取图片的尺寸
    width, height = image.size
    # 限定尺寸的阈值
    limit_small = 512
    limit_short = 768
    limit_long = 2000
    # 决定是否需要改变图片尺寸的标记
    resize_flag = False
    new_size = width, height
    if mode == "low":
        if max(width, height) > limit_small:
            new_size = limit_small, limit_small
            resize_flag = True
    elif mode == "high":
        if min(width, height) > limit_short or max(width, height) > limit_long:
            new_size = min(limit_short, width), min(limit_long, height)
            resize_flag = True
    elif mode == "auto":
        if limit_small < max(width, height) < limit_short:
            new_size = limit_small, limit_small
            resize_flag = True
        elif min(width, height) > limit_short or max(width, height) > limit_long:
            new_size = min(limit_short, width), min(limit_long, height)
            resize_flag = True
    if resize_flag:
        image.thumbnail(new_size, Image.Resampling.BICUBIC)
    bytes_io = BytesIO()
    image.save(bytes_io, format="PNG")
    bytes_return = bytes_io.getvalue()
    return bytes_return
