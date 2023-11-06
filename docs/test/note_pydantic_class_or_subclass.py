# -*- coding: utf-8 -*-
# @Time    : 2023/9/21 下午11:34
# @Author  : sudoskys
# @File    : type_tes.py
# @Software: PyCharm
from pydantic import BaseModel


class Base(BaseModel):
    at = 0


class Base2(Base):
    ut = 1

    @property
    def att(self):
        return 1


def test():
    return 1


if __name__ == '__main__':
    print(isinstance(Base2(), Base))
    print(isinstance(Base(), Base2))
    print(hasattr(Base(), 'att'))
    print([Base2()])
    assert isinstance(Base2(), Base)
