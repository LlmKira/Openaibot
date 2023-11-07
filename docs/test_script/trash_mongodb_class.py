# -*- coding: utf-8 -*-
# @Time    : 2023/10/27 上午1:04
# @Author  : sudoskys
# @File    : test_mongodb.py
# @Software: PyCharm
from llmkira.extra.user.client import UserConfigClient
from llmkira.extra.user import UserConfig

if __name__ == '__main__':
    async def main():
        _es = await UserConfigClient().read_by_uid("test2")
        print(_es)
        test2 = UserConfig(uid="test2",
                           created_time=0)
        test2_ = await UserConfigClient().update(uid="test2", data=test2)
        print(test2_)


    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
