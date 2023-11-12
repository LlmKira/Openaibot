# -*- coding: utf-8 -*-
# @Time    : 2023/11/12 下午9:12
# @Author  : sudoskys
# @File    : pydantic_feat.py
# @Software: PyCharm
from pydantic import field_validator, BaseModel, ValidationError


class UserModel(BaseModel):
    id: int
    name: str

    @field_validator('name')
    def name_must_contain_space(cls, v: str) -> str:
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()


try:
    UserModel(id=0, name='JohnDoe')
except ValidationError as e:
    print(e)
