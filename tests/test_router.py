# -*- coding: utf-8 -*-
# @Time    : 2023/11/14 下午3:05
# @Author  : sudoskys
# @File    : test_router.py
# @Software: PyCharm
import sys

sys.path.append("..")
from llmkira.middleware.router import RouterCache, Router  # noqa: E402


def test_schema():
    r1 = RouterCache(router=[])
    print("\n")
    print(r1)
    try:
        RouterCache(router=None)
    except Exception:
        pass
    else:
        assert False, "Should Raise Error"

    r3 = Router(from_="from", to_="to", user_id=2200, rules="rule there", method="chat")
    print("\n")
    print(r3)
