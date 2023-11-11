# -*- coding: utf-8 -*-
# @Time    : 2023/11/11 下午3:42
# @Author  : sudoskys
# @File    : pydantic_mo.py
# @Software: PyCharm
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    age: Optional[int] = None


if __name__ == '__main__':
    u1 = User(id=1, name="sudoskys")
    u11 = User(id=1, name="sudoskys")
    u2 = User(id=2, name="sudoskys", age=18)
    u3 = User(id=3, name="sudoskys", age=18)
    print(u1 == u11)
    l1 = [u1, u2]
    print(u1 in l1)
    l1.remove(u11)
    print(l1)
