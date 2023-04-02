# -*- coding: utf-8 -*-
# @Time    : 2023/4/1 下午9:58
# @Author  : sudoskys
# @File    : keymanager.py
# @Software: PyCharm
from typing import Set, List, Dict, Optional, Any, Union, Literal
from pydantic import (
    BaseModel,
    BaseSettings,
    PyObject,
    RedisDsn,
    Field, validator,
)


class ApiKeySettings(BaseModel):
    # Openai Key with title ,dict
    Openai: Dict[str, str] = Field(default_factory=dict)

    @validator('Openai')
    def check_openai(cls, v):
        # 循环列表，弹出非法值（不以 sk- 开头的）
        for key in list(v.keys()):
            if not key.startswith("sk-"):
                v.pop(key)
        return v

    def openai(self, title: str) -> Optional[str]:
        return self.Openai.get(title, None)


if __name__ == '__main__':
    a = ApiKeySettings()
    print(a.json())
