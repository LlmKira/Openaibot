# -*- coding: utf-8 -*-
import os
import re
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from types import ModuleType
from typing import Optional, Type, Dict, Any, List, Union, Set, final
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import field_validator, BaseModel, Field, model_validator

from llmkira.openai.cell import Tool, ToolCall
from llmkira.openai.request import OpenAIResult

if TYPE_CHECKING:
    from llmkira.task.schema import TaskHeader, Location
    from .model import PluginManager


class BaseTool(ABC, BaseModel):
    """
    基础工具类，所有工具类都应该继承此类
    """

    __slots__ = ()
    silent: bool = False
    """If True, the tool will not be displayed in the help message"""

    function: Union[Tool, Type[BaseModel]]
    """The function schema to be executed"""

    @final
    @field_validator("function", mode="after")
    def _check_function(cls, v):
        if issubclass(v, BaseModel):
            v = Tool(function=v)
        elif isinstance(v, Tool):
            pass
        else:
            raise ValueError(f"function must be Tool or BaseModel, got {type(v)}")
        return v

    keywords: List[str] = []
    """The keyword list to be matched to load tools in session"""

    @final
    @field_validator("keywords")
    def _check_keywords(cls, v):
        for i in v:
            if len(i) < 2:
                logger.warning(f"keyword should be more than 2 characters, got {i}")
        return v

    pattern: Optional[re.Pattern] = None
    """The pattern to be matched to load tools in session"""

    env_required: List[str] = Field([], description="环境变量要求,ALSO NEED env_prefix")
    """Pre-required environment variables, you should provide env_prefix"""

    env_prefix: str = Field("", description="环境变量前缀")
    """Environment variable prefix"""

    file_match_required: Optional[re.Pattern] = Field(
        None, description="re.compile 文件名正则"
    )
    """File name regular expression to use the tool, exp: re.compile(r"file_id=([a-z0-9]{8})")"""

    def require_auth(self, env_map: dict) -> bool:
        """
        Check if authentication is required
        """
        return True

    @final
    def get_os_env(self, env_name):
        """
        Get environment variables from os.environ
        """
        env = os.getenv("PLUGIN_" + env_name, None)
        return env

    @final
    @property
    def env_list(self):
        """
        Return the env_prefix+env_name list
        #🍪# If you think its cant be final, you can issue it.
        """
        return [f"{self.env_prefix}{env_name}" for env_name in self.env_required]

    @final
    @property
    def name(self):
        """
        Tool name
        """
        return self.function.function.name

    @final
    @model_validator(mode="after")
    def _check_conflict(self):
        if self.silent and self.env_required:
            # raise ValueError("silent and env_required can not be True at the same time")
            logger.warning(
                "\n Plugin `silent` And `env_required` Should Not Be True Same Time"
                "Please Validate `env_required` In Execute Manual, Or Provide Callback To User Instead"
            )
        if self.env_required and not self.env_prefix:
            raise ValueError("env_required must be used with env_prefix")
        return self

    @classmethod
    def env_help_docs(cls, empty_env: List[str]) -> Optional[str]:
        """
        Provide help message for environment variables
        :param empty_env: The environment variable list that not configured
        :return: The help message or None
        """
        assert isinstance(empty_env, list), "empty_env must be list"
        if not empty_env:
            return None
        return "You need to configure ENV to start use this tool"

    @abstractmethod
    def func_message(self, message_text, message_raw, address, **kwargs):
        """
        If the message_text contains the keyword, return the function to be executed, otherwise return None
        :param message_text: 消息文本
        :param message_raw: 消息原始数据 `EventMessage`
        :param address: 消息地址 `tuple(sender,receiver)`
        :param kwargs :
        message_raw: 消息原始数据 `EventMessage`
        address: 消息地址 `tuple(sender,receiver)`
        """
        for word in self.keywords:
            if word in message_text:
                return self.function
        # Regrex Match
        if self.pattern:
            match = self.pattern.match(message_text)
            if match:
                return self.function
        _ignore = kwargs
        return None

    @abstractmethod
    async def failed(
        self,
        task: "TaskHeader",
        receiver: "Location",
        exception,
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
    ):
        """
        通常为 回写消息+通知消息
        :param task: 任务
        :param receiver: 接收者
        :param exception: 异常
        :param env: 环境变量
        :param arg: 参数
        :param pending_task: 任务批次
        :param refer_llm_result: 上一次的结果
        """
        _ignore = task, receiver, env, arg, pending_task, refer_llm_result, exception
        return ...

    @abstractmethod
    async def callback(
        self,
        task: "TaskHeader",
        receiver: "Location",
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
    ):
        """
        运行成功会调用此函数
        :param task: 任务
        :param receiver: 接收者
        :param arg: 参数
        :param env: 环境变量
        :param pending_task: 任务批次
        :param refer_llm_result: 上一次的结果
        """
        _ignore = task, receiver, env, arg, pending_task, refer_llm_result
        return ...

    @abstractmethod
    async def run(
        self,
        *,
        task: "TaskHeader",
        receiver: "Location",
        arg: dict,
        env: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
    ):
        """
        处理函数并返回回写结果
        :param task: 任务
        :param receiver: 接收者
        :param arg: 参数
        :param env: 环境变量
        :param pending_task: 任务批次
        :param refer_llm_result: 上一次的结果
        """
        _ignore = task, receiver, env, arg, pending_task, refer_llm_result
        return ...

    @final
    async def load(
        self,
        *,
        task: "TaskHeader",
        receiver: "Location",
        arg: dict,
        env: dict = None,
        pending_task: "ToolCall",
        refer_llm_result: Union[OpenAIResult, dict] = None,
        **kwargs,
    ) -> dict:
        """
        加载工具，执行前的准备工作
        :param task: 任务
        :param receiver: 接收者
        :param arg: 参数
        :param env: 环境变量
        :param pending_task: 任务批次
        :param refer_llm_result: 上一次的结果
        :param kwargs: 额外参数
        :return: 运行结果
        """
        if not env:
            env = {}
        # 拒绝循环引用, 复制一份传递
        run_pipe = {
            "task": task.model_copy(deep=True),
            "receiver": receiver.model_copy(deep=True),
            "arg": arg,
            "env": env,
            "pending_task": pending_task.model_copy(deep=True),
            "refer_llm_result": refer_llm_result,
        }
        run_pipe.update(kwargs)
        try:
            run_result = await self.run(**run_pipe)
        except Exception as e:
            logger.exception(e)
            logger.error(f"ToolExecutor:run error: {e}")
            run_pipe["exception"] = str(e)
            await self.failed(**run_pipe)
        else:
            run_pipe["result"] = run_result
            try:
                await self.callback(**run_pipe)
            except Exception as e:
                logger.error(f"ToolExecutor:callback error: {e}")
        return run_pipe


@dataclass(eq=False)
class FuncPair:
    function: Union[Tool]
    tool: Type[BaseTool]
    extra_arg: Dict[Any, Any] = field(default_factory=dict)

    @property
    def name(self):
        return self.function.function.name


class PluginMetadata(BaseModel):
    """
    插件元信息，由插件编写者提供
    """

    name: str = Field(..., max_length=20)
    """插件名称"""
    description: str = Field(..., max_length=200)
    """插件功能介绍"""
    usage: str = Field(..., max_length=300)
    """插件使用方法"""
    openapi_version: str = Field(..., max_length=10)
    """适应版本"""
    function: Set[FuncPair] = Field(default_factory=set)
    """插件工具"""
    type: Optional[str] = None
    """插件类型"""
    homepage: Optional[str] = Field(None, max_length=50)
    """插件主页"""
    config: Optional[Type[BaseModel]] = None
    """插件配置项"""
    extra: Dict[Any, Any] = Field(default_factory=dict)
    """插件额外信息，可由插件编写者自由扩展定义"""

    @model_validator(mode="before")
    def limit(cls, values):
        if len(values.get("function", [])) == 0:
            raise ValueError("function can not be empty")
        if not values.get("openapi_version", None):
            raise ValueError("openapi_version can not be empty")
        if len(values.get("description", "")) > 200:
            raise ValueError("description must be less than 200 characters")
        if len(values.get("usage", "")) > 300:
            raise ValueError("usage must be less than 300 characters")
        return values

    @property
    def get_function_string(self) -> str:
        return "include{" + ",".join([f"{i.name}" for i in self.function]) + "}"


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
