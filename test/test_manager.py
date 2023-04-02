# -*- coding: utf-8 -*-
# @Time    : 2023/4/1 下午6:18
# @Author  : sudoskys
# @File    : test_manager.py
# @Software: PyCharm
import pytest
import asyncio

from Handler.manager import UserManager
from utils.setting.user import UserConfig


def test_user_manager():
    async def main():
        user_manager = UserManager()
        # 测试保存和读取新用户
        new_user = UserConfig(uid=1, name="Alice")
        await user_manager.save(new_user)
        loaded_user = await user_manager.read(1)
        assert loaded_user == new_user

        # 测试更新已有用户信息
        updated_user = UserConfig(uid=1, quota=20, name="New York")
        await user_manager.save(updated_user)
        loaded_user = await user_manager.read(1)
        assert loaded_user == updated_user

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
