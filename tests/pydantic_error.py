# -*- coding: utf-8 -*-
# @Time    : 2024/1/17 上午11:52
# @Author  : sudoskys
# @File    : pydantic_error.py
# @Software: PyCharm
from pprint import pprint
from typing import Optional, Literal

from pydantic import BaseModel


class ContentParts(BaseModel):
    """
    请求体
    """

    class Image(BaseModel):
        url: str
        detail: Optional[Literal["low", "high", "auto"]] = "auto"

    type: str
    text: Optional[str]
    image_url: Optional[Image]


try:
    ContentParts(type="text", text="testing")
except Exception as e:
    pprint(e)
    """
    1 validation error for ContentParts
image_url
  Field required [type=missing, input_value={'type': 'text', 'text': 'testing'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.5/v/missing
    """

try:
    ContentParts(
        type="image", image_url=ContentParts.Image(url="https://www.baidu.com")
    )
except Exception as e:
    pprint(e)
    """
    1 validation error for ContentParts
text
  Field required [type=missing, input_value={'type': 'image', 'image_...du.com', detail='auto')}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.5/v/missing

    """


class ContentPartsAnother(BaseModel):
    """
    请求体
    """

    text: str
    image: Optional[bool] = None


try:
    pprint(ContentPartsAnother(text="testing").model_dump_json())
except Exception as e:
    pprint(e)
    """
    '{"text":"testing","image":null}'
    """
