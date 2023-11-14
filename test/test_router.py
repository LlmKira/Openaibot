# -*- coding: utf-8 -*-
# @Time    : 2023/11/14 下午3:05
# @Author  : sudoskys
# @File    : test_router.py
# @Software: PyCharm
import sys

from llmkira.middleware.router import RouterCache, Router

sys.path.append("..")

def test_schema():
    r1 = RouterCache(
        router=[]
    )
    print("\n")
    print(r1)
    try:
        RouterCache(
            router=None
        )
    except Exception as e:
        pass
    else:
        assert False, "Should Raise Error"

    r3 = Router(
        from_="from",
        to_="to",
        user_id=2200,
        rules="rule there",
        method="chat"
    )
    print('\n')
    print(r3)
