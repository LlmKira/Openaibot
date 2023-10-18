# -*- coding: utf-8 -*-

import re
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from types import ModuleType
from typing import Optional, Type, Dict, Any, List, Union, Set, final, Literal

from pydantic import BaseModel, Field, validator, root_validator

from ..schema import Function


class BaseTool(ABC, BaseModel):
    """
    基础工具类，所有工具类都应该继承此类
    """
    __slots__ = ()
    silent: bool = Field(False, description="是否静默")
    function: Function = Field(..., description="功能")
    keywords: List[str] = Field([], description="关键词")
    pattern: Optional[re.Pattern] = Field(None, description="正则匹配")
    require_auth: bool = Field(False, description="是否需要授权")
    repeatable: bool = Field(False, description="是否可重复使用")
    deploy_child: Literal[0, 1] = Field(1, description="如果为0，终结于此链点，不再向下传递")
    require_auth_kwargs: dict = {}
    env_required: List[str] = Field([], description="环境变量要求")

    @final
    @property
    def name(self):
        """
        工具名称
        """
        return self.function.name

    def env_help_docs(self, empty_env: List[str]) -> str:
        """
        环境变量帮助文档
        :param empty_env: 未被配置的环境变量列表
        :return: 帮助文档/警告
        """
        assert isinstance(empty_env, list), "empty_env must be list"
        return "You need to configure ENV to start use this tool"

    @final
    @root_validator
    def check_conflict(cls, values):
        # env_required and silent
        if values["silent"] and values["env_required"]:
            raise ValueError("silent and env_required can not be True at the same time")
        return values

    @final
    @validator("keywords", pre=True)
    def check_keywords(cls, v):
        for i in v:
            if not isinstance(i, str):
                raise ValueError(f"keyword must be str, got {type(i)}")
            if len(i) > 20:
                raise ValueError(f"keyword must be less than 20 characters, got {len(i)}")
            if len(i) < 2:
                raise ValueError(f"keyword must be more than 2 characters, got {len(i)}")
        return v

    @abstractmethod
    def pre_check(self) -> Union[bool, str]:
        """
        预检查，如果不合格则返回 False，合格则返回 True
        返回字符串表示不合格，且有原因
        """
        return ...

    @abstractmethod
    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        # 正则匹配
        if self.pattern:
            match = self.pattern.match(message_text)
            if match:
                return self.function
        return None

    @abstractmethod
    async def failed(self, platform, task, receiver, reason):
        """
        处理失败
        """
        return ...

    @abstractmethod
    async def run(self, task, receiver, arg, **kwargs):
        """
        处理message，返回message
        """
        env = kwargs.get("env", {})
        return ...

    @abstractmethod
    async def callback(self, sign: str, task):
        """
        回调
        """
        return ...

    @final
    async def load(self, task, receiver, arg, env: dict = None, **kwargs):
        if not env:
            env = {}
        await self.run(
            task=task,
            receiver=receiver,
            arg=arg,
            env=env
        )


@dataclass(eq=False)
class FuncPair:
    function: Function
    tool: Type[BaseTool]
    extra_arg: Dict[Any, Any] = field(default_factory=dict)

    @property
    def name(self):
        return self.function.name


@dataclass(eq=False)
class PluginMetadata:
    """
    插件元信息，由插件编写者提供
    """

    name: str
    """插件名称"""
    description: str
    """插件功能介绍"""
    usage: str
    """插件使用方法"""
    openapi_version: str
    """适应版本"""
    function: Set[FuncPair] = field(default_factory=set)
    """插件工具"""
    type: Optional[str] = None
    """插件类型"""
    homepage: Optional[str] = None
    """插件主页"""
    config: Optional[Type[BaseModel]] = None
    """插件配置项"""
    extra: Dict[Any, Any] = field(default_factory=dict)
    """插件额外信息，可由插件编写者自由扩展定义"""


@dataclass(eq=False)
class Plugin:
    """
    机制用途，不由用户实例化
    """

    name: str
    """插件索引标识，Bot 使用 文件/文件夹 名称作为标识符"""
    module: ModuleType
    """插件模块对象"""
    module_name: str
    """点分割模块路径"""
    manager: "PluginManager"
    """导入该插件的插件管理器"""
    parent_plugin: Optional["Plugin"] = None
    """父插件"""
    sub_plugins: Set["Plugin"] = field(default_factory=set)
    """子插件集合"""
    metadata: Optional[PluginMetadata] = None
    """插件元信息"""

# 探针插件加载机制 参考 nonebot2 项目设计
