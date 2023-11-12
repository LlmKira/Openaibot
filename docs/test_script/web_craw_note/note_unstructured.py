# -*- coding: utf-8 -*-
# @Time    : 2023/11/6 下午9:21
# @Author  : sudoskys
# @File    : note_unstructured.py
# @Software: PyCharm
from typing import List, Optional

from pydantic import BaseModel, Field
from rich import print
from unstructured.partition import auto

test_url_list = [
    "https://blog.cuijiacai.com/blog-building/",
    "https://github.com/LlmKira/Openaibot",
    "https://react.dev/learn/tutorial-tic-tac-toe",
    "https://blog.csdn.net/weixin_39198406/article/details/106418574",
]


class UnstructuredElement(BaseModel):
    class Meta(BaseModel):
        url: str
        title: Optional[str] = Field(None, alias="title")
        filetype: Optional[str] = Field(None, alias="filetype")
        page_number: int = Field(None, alias="page_number")
        languages: List[str] = Field(None, alias="languages")
        category_depth: int = Field(None, alias="category_depth")
        link_urls: List[str] = Field(None, alias="link_urls")
        link_texts: Optional[str] = Field(None, alias="link_text")

    text: str
    metadata: Meta
    element_id: str
    type: str

    class Config:
        extra = "ignore"

    @classmethod
    def from_element(cls, anything):
        return cls(**anything.to_dict())


def autos():
    for url in test_url_list:
        print(f"\ntest url is {url}")
        elements = auto.partition(url=url)
        titled = False
        for element in elements:
            obj = UnstructuredElement.from_element(element)
            if len(obj.text.strip().strip("\n")) > 5:
                if obj.type != "Title":
                    titled = True
                else:
                    if titled:
                        continue
                print(obj.text)

        print("=====================================\n")
        assert len(elements) > -1


autos()
