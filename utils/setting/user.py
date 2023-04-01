# -*- coding: utf-8 -*-
# @Time    : 2023/3/31 下午9:28
# @Author  : sudoskys
# @File    : user.py
# @Software: PyCharm

import base64
from typing import Union

from pydantic import BaseModel


# 人员单点为中心，采用 初始quota+个人可提额 设计

# 给群组标记访问权限，同样给个人标记访问权限

# 可以/不可以


class ChatSystemConfig(BaseModel):
    public_group_access: bool = True
    public_chat_access: bool = True
    # 群聊权限
    service_on: bool = True
    # 服务开关
    input_limit: int = 500
    # 输入限制
    output_limit: int = 1000
    # 输出限制
    user_rate_limit: int = 0
    # 限制频率
    group_rate_limit: int = 0
    # 群组冷却时间
    allow_design_role: bool = True
    # 允许设计角色
    quota: int = 300  # 饼干
    # 换算额度顶峰，和用户额度比较，取最大值


class UserConfig(BaseModel):
    public_chat_access: bool = False
    # 用户权限组
    uid: int
    # 用户ID
    name: str = base64.b64encode("猫娘".encode("utf-8"))
    # 用户名
    media: bool = False
    # 多媒体
    usage: int = 0
    # 通过换算器换算后的用量
    quota: int = 0
    # 额度，和全局设置比较，取最大值


class GroupConfig(BaseModel):
    uid: int
    # 群组ID
    public_group_access: bool = False
    # 权限组
    cross: bool = True
    # 跨消息
    trace: bool = False
    # 跟踪特定用户
    silent: bool = False
    # 服务消息静默
    trigger: bool = False
    # 自动触发


# 当两方都有权限才能访问
def get_access(service: Union[UserConfig, GroupConfig], chat_system_config: ChatSystemConfig):
    if isinstance(service, UserConfig):
        return service.public_chat_access or chat_system_config.public_chat_access
    if isinstance(service, GroupConfig):
        return service.public_group_access or chat_system_config.public_group_access
    return False


def get_quota(service: Union[UserConfig], chat_system_config: ChatSystemConfig):
    return max(service.quota, chat_system_config.quota)


def covert_usage_to_quota(usage: int, price: int):
    """
    换算器, 用量换算额度，单位是
    :param usage: 每 1k
    :param price: 定价，来自模型 service 设置
    :return: 额度
    """
    return usage * price
