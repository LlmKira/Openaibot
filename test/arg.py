# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 下午1:46
# @Author  : sudoskys
# @File    : arg.py.py
# @Software: PyCharm
from pydantic import BaseModel, Field


class Search(BaseModel):
    """
    测试搜索类型
    """
    keywords: str = Field(None, description="关键词")
    text: str = Field(None, description="文本")

    def run(self):
        return self.keywords + self.text


print(Search.schema())
