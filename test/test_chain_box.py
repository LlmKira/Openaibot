# -*- coding: utf-8 -*-
# @Time    : 2023/11/14 上午11:31
# @Author  : sudoskys
# @File    : test_chain_box.py
# @Software: PyCharm
import sys
from pprint import pprint

from llmkira.middleware import chain_box
from llmkira.task.schema import TaskHeader

sys.path.append("..")


def test_schema():
    arg = TaskHeader(sender=TaskHeader.Location(),
                     receiver=TaskHeader.Location()
                     )
    print('\n')
    pprint(arg)
    try:
        chain_box.schema.Chain(
            arg=arg,
            channel="5slist",
            creator_uid="550w",
        )
    except Exception as e:
        pprint(f"As Expected {str(e)}")
    else:
        assert False, "Should Raise Error"
    test_obj = chain_box.schema.Chain(
        arg=arg,
        channel="5slist",
        creator_uid="platform:2225",
    )
    print('\n')
    pprint(test_obj)
