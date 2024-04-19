# -*- coding: utf-8 -*-
# @Time    : 2023/10/14 下午2:16
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import time
from enum import Enum
from typing import TYPE_CHECKING, Dict
from typing import Tuple, List, Union, Optional

import shortuuid
from loguru import logger
from pydantic import model_validator, ConfigDict, Field, BaseModel

from llmkira.kv_manager.file import File
from llmkira.openai.cell import (
    UserMessage,
    ToolMessage,
    ToolCall,
    Tool,
    ContentPart,
    AssistantMessage,
)
from llmkira.openai.request import OpenAIResult

if TYPE_CHECKING:
    pass


class EventMessage(BaseModel):
    """
    Event Message for mq database
    """

    user_id: Union[str] = Field(None, description="User id")
    chat_id: Union[str] = Field(None, description="Chat id")
    thread_id: Optional[Union[str]] = Field(
        None, description="Channel ID(slack thread)"
    )
    text: str = Field("", description="Text of message")
    files: List[File] = Field([], description="File(ID*) of message")
    created_at: str = Field(
        default_factory=lambda: str(int(time.time())), description="Create time"
    )

    model_config = ConfigDict(arbitrary_types_allowed=False, extra="allow")

    # only_send_file: bool = Field(default=False, description="Send file only")
    # sign_loop_end: bool = Field(default=False, description="要求其他链条不处理此消息，用于拦截器开发")
    # sign_fold_docs: bool = Field(default=False, description="是否获取元数据")

    async def format_user_message(self, name: str = None) -> UserMessage:
        """Format message to UserMessage"""
        content_list = [ContentPart.create_text(self.text)]
        if self.files:
            for file in self.files:
                if file.file_name.endswith((".jpg", ".jpeg", ".png")):
                    file_bytes = await file.download_file()
                    try:
                        content_list.append(ContentPart.create_image(file_bytes))
                    except Exception as e:
                        logger.error(f"Error when create image: {e}")
        return UserMessage(
            role="user",
            name=name,
            content=content_list,
        )

    @classmethod
    def from_openai_message(
        cls, message: AssistantMessage, locate: "Location"
    ) -> "EventMessage":
        """
        用于 OpenAI 消息转换回复给用户
        """
        return cls(
            user_id=locate.user_id,
            text=message.content,
            chat_id=locate.chat_id,
            created_at=str(int(time.time())),
        )


class ToolResponse(BaseModel):
    """
    Tool Callback for plugin tool
    # TODO:携带自身工具，供我们重组上下文工具时mock使用。
    """

    name: str = Field(description="功能名称", pattern=r"^[a-zA-Z0-9_]+$")
    function_response: str = Field("[empty response]", description="工具响应内容")
    tool_call_id: str = Field(description="工具调用ID")
    tool_call: ToolCall = Field(description="工具调用")

    def format_tool_message(self) -> Union[ToolMessage]:
        if self.tool_call_id:
            return ToolMessage(
                tool_call_id=self.tool_call_id, content=self.function_response
            )
        raise ValueError("tool_call_id is empty")


class Router(Enum):
    REPLIES = "replies"  # 回复消息
    DELIVER = "deliver"  # 只通知，不重组函数和初始化任何东西。
    REPROCESS = "reprocess"  # 回写消息，释放任务链，要求再次处理
    ANSWER = "answer"  # 回复消息


class Sign(BaseModel):
    sign_as: Tuple[int, str, str, str] = Field(
        default=(0, "root", "default", str(shortuuid.uuid()).upper()[:5]),
        description="签名",
    )
    """当前链条的层级"""

    instruction: Optional[str] = Field(None, description="指令")
    """System Prompt"""

    disable_tool_action: bool = False
    """Toolcall 是否被禁用"""

    tool_response: List[ToolResponse] = Field(
        default=[], description="用于回写，插件返回的消息头，标识 function 的名字"
    )
    """工具响应"""

    memory_able: bool = False
    """是否写回数据库"""

    router: Router = Field(Router.ANSWER, description="路由规则")
    """路由规则"""

    response_snapshot: bool = Field(False, description="是否响应函数快照")
    """接收器是否响应函数快照"""

    tools_ghost: List[Tool] = Field([], description="工具集")
    """工具集"""

    # resign_next_step: bool = Field(False, description="函数集群是否可以继续拉起其他函数集群")
    tool_calls_counter: int = Field(0, description="函数集群计数器")
    """函数响应计数"""

    tool_calls_limit: int = Field(5, description="函数集群计数器上限")
    """函数响应限制"""

    tool_calls_pending: List[ToolCall] = Field([], description="函数快照")
    """待处理的函数响应"""

    tool_calls_completed: List[Tuple[ToolCall, bool, Union[str, dict]]] = Field(
        default=[], description="完成的节点状态"
    )
    """完成的函数响应"""

    # tool_calls_completed: List[ToolCall] = Field([], description="完成的函数快照")
    snapshot_credential: Optional[str] = Field(
        None, description="认证链的UUID，根据此UUID和 Map 可以确定哪个需要执行"
    )
    """当前待处理的函数"""

    certify_needed_map: Dict[str, ToolCall] = Field(
        {}, description="Snapshot Map for uuid, toolcall"
    )
    """认证地图，需要快照"""

    llm_response: Optional[OpenAIResult] = Field(None, description="OpenAI Response")
    """原生响应"""

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=False)

    @property
    def task_uuid(self):
        return self.sign_as[3]

    @property
    def layer(self):
        return self.sign_as[0]

    @property
    def tools(self):
        return self.tools_ghost

    @model_validator(mode="after")
    def validate_param(self):
        # If it is the root node, it cannot be written back.
        # Because the message posted by the user is always the root node.
        # Writing back will cause duplicate messages.
        if self.sign_as[0] == 0 and self.memory_able:
            logger.warning("root node cant write back")
            self.memory_able = False
        return self

    def child(self, name: str) -> "Sign":
        """
        生成子节点，继承父节点的功能
        """
        self.sign_as = (self.sign_as[0] + 1, "child", name, self.sign_as[3])
        return self.model_copy(deep=True)

    def snapshot(self, name, memory_able: bool, response_snapshot: bool) -> "Sign":
        """
        快照
        """
        self.sign_as = (self.sign_as[0] + 1, "chain", name, self.sign_as[3])
        self.router = Router.ANSWER
        self.memory_able = memory_able
        self.response_snapshot = response_snapshot
        return self.model_copy(deep=True)

    @classmethod
    def from_root(
        cls,
        response_snapshot: bool,
        disable_tool_action: bool,
        platform: str = "default",
    ) -> "Sign":
        """
        构造函数，从根节点生成
        :param response_snapshot: 是否响应函数快照
        :param disable_tool_action: 是否禁用工具调用
        :param platform: 平台
        """
        node_uuid = str(shortuuid.uuid()).upper()[:5]
        return cls(
            sign_as=(0, "root", platform, node_uuid),
            response_snapshot=response_snapshot,
            disable_tool_action=disable_tool_action,
        )

    def update_tool_calls(
        self,
        *,
        tool_calls: List[ToolCall],
        certify_needed_map: dict,
    ) -> "Sign":
        """
        更新快照
        :param tool_calls: 快照
        :param certify_needed_map: 快照Map
        :return: Sign
        :raise ValueError: 快照不能为空
        """
        if not certify_needed_map:
            certify_needed_map = self.certify_needed_map
        if not tool_calls:
            raise ValueError("plan_chain_pending can't be empty")
        copy_model = self.model_copy(deep=True)
        copy_model.certify_needed_map = certify_needed_map
        copy_model.tool_calls_pending = tool_calls
        return copy_model

    def update_state(
        self,
        router: Router = None,
        instruction: str = None,
        disable_tool_action: bool = None,
        memory_able: bool = None,
        response_snapshot: bool = None,
        tool_calls: List[ToolCall] = None,
        tool_response: List[ToolResponse] = None,
        tools_ghost: List[Tool] = None,
    ) -> "Sign":
        """
        更新状态，用于统一管理状态
        """
        if router:
            self.router = router
        if instruction:
            self.instruction = instruction
        if disable_tool_action is not None:
            self.disable_tool_action = disable_tool_action
        if memory_able is not None:
            self.memory_able = memory_able
        if response_snapshot is not None:
            self.response_snapshot = response_snapshot
        if tool_calls:
            self.tool_calls_pending = tool_calls
        if tool_response:
            self.tool_response = tool_response
        if tools_ghost:
            self.tools_ghost = tools_ghost
        return self

    def notify(
        self,
        *,
        plugin_name: str,
        tool_response: List[ToolResponse] = None,
        response_snapshot: bool,
        disable_tool_action: bool = False,
        memory_able: bool = None,
    ):
        """
        Deliver message, release task chain, reply message
        :param plugin_name: Plugin name
        :param tool_response: The response of the tool
        :param memory_able : Whether to write back to history
        :param response_snapshot: 是否释放任务链，是否释放任务链，比如插件运行失败，错误消息发送的同时需要释放任务链防止挖坟
        :param disable_tool_action: If the robot is allowed to call tools again
        :return: Sign
        """
        if tool_response is not None:
            assert isinstance(tool_response, list), "callback must be list"
        return self.child(plugin_name).update_state(
            router=Router.DELIVER,
            memory_able=memory_able,
            response_snapshot=response_snapshot,
            disable_tool_action=disable_tool_action,
            tool_response=tool_response,
        )

    def reprocess(
        self,
        *,
        plugin_name: str,
        tool_response: List[ToolResponse],
        disable_tool_action: bool = False,
    ):
        """
        Reply message, reprocess message raw format, suitable for json/yaml response
        :param plugin_name: Plugin name
        :param tool_response: The response of the tool
        :param disable_tool_action: If the robot is allowed to call tools again
        """
        assert isinstance(tool_response, list), "callback must be list"
        return self.child(plugin_name).update_state(
            tool_response=tool_response,
            router=Router.REPROCESS,
            memory_able=True,
            response_snapshot=True,
            disable_tool_action=disable_tool_action,
        )

    def reply(
        self,
        *,
        plugin_name: str,
        tool_response: List[ToolResponse],
        disable_tool_action: bool = False,
    ):
        """
        决定路由规则
        回写消息，释放任务链，回复消息
        :param plugin_name: 插件名称
        :param tool_response: 元信息
        :param disable_tool_action: 是否允许机器人用函数再次处理
        """
        assert isinstance(tool_response, list), "callback must be list"
        return self.child(plugin_name).update_state(
            tool_response=tool_response,
            router=Router.REPLIES,
            memory_able=True,
            response_snapshot=True,
            disable_tool_action=disable_tool_action,
        )

    async def get_pending_tool_call(
        self, credential: str, return_default_if_empty: bool = False
    ) -> Optional[ToolCall]:
        """
        获取当前待处理的函数
        """
        if not self.tool_calls_pending:
            logger.debug("tool_calls is empty")
            return None
        if credential in self.certify_needed_map:
            return self.certify_needed_map[credential]
        if return_default_if_empty:
            return self.tool_calls_pending[0]
        return None

    async def complete_task(
        self, tool_calls: ToolCall, success_or_not: bool, run_result: Union[str, dict]
    ) -> "Sign":
        """
        完成此集群
        self.plan_chain_archive.append((task_batch, run_result))
        if task_batch in self.plan_chain_pending:
            self.plan_chain_pending.remove(task_batch)
        if not self.plan_chain_pending:
            self.plan_chain_complete = True
        :return: Sign
        """
        self.tool_calls_completed.append((tool_calls, success_or_not, run_result))
        if tool_calls in self.tool_calls_pending:
            self.tool_calls_pending.remove(tool_calls)
        return self

    def get_snapshot_credential(self, tool_calls: ToolCall) -> Optional[str]:
        """
        从 Map 获取验证UUID
        """
        for key, item in self.certify_needed_map.items():
            if item == tool_calls:
                return key
        return None


class Location(BaseModel):
    """
    here .... channel
    """

    platform: str = Field(None, description="platform")
    user_id: str = Field(None, description="user id")
    chat_id: str = Field(None, description="guild id(channel in dm)/Telegram chat id")
    thread_id: Optional[str] = Field(None, description="channel id/Telegram thread")
    message_id: Optional[str] = Field(None, description="message id")

    @model_validator(mode="after")
    def to_string(self):
        for key in ["user_id", "chat_id", "thread_id", "message_id"]:
            if isinstance(getattr(self, key), int):
                setattr(self, key, str(getattr(self, key)))
        return self

    @property
    def uid(self):
        return f"{self.platform}:{self.user_id}"


class Plugin(BaseModel):
    name: str = Field(None, description="插件名称")
    is_run_out: bool = Field(False, description="是否运行完毕")
    token_usage: int = Field(0, description="Token 用量")


class TaskHeader(BaseModel):
    """
    任务链节点
    """

    task_sign: Sign = Field(Sign(), description="任务元数据")
    sender: Location = Field(..., description="发信人")
    receiver: Location = Field(..., description="接收人")
    message: List[EventMessage] = Field(None, description="消息内容")

    @classmethod
    def from_sender(
        cls,
        event_messages: List[EventMessage],
        task_sign: Sign,
        message_id: Optional[str],
        chat_id: str,
        user_id: str,
        platform: str,
    ):
        """
        从telegram消息中构建任务
        """
        return cls(
            task_sign=task_sign,
            sender=Location(
                platform=platform,
                chat_id=chat_id,
                user_id=user_id,
                message_id=message_id,
            ),
            receiver=Location(
                platform=platform,
                chat_id=chat_id,
                user_id=user_id,
                message_id=message_id,
            ),
            message=event_messages,
        )

    @classmethod
    def from_function(
        cls,
        llm_response: OpenAIResult,
        task_sign: Sign,
        receiver: Location,
        message: List[EventMessage] = None,
    ):
        """
        从 Openai LLM Task中构建任务
        """
        # task_sign = task_sign.child("function") 发送到 function 的消息不需加点，因为此时 接收器算发送者
        task_sign.llm_response = llm_response
        return cls(
            task_sign=task_sign, sender=receiver, receiver=receiver, message=message
        )


class Snapshot(BaseModel):
    """
    快照
    """

    snap_uuid: str = Field(
        default_factory=lambda: str(shortuuid.uuid()).upper()[:5],
        description="快照UUID",
    )
    snapshot_credential: Optional[str] = None
    snapshot_data: TaskHeader
    creator: str
    channel: str
    expire_at: int
    created_at: int = Field(default_factory=lambda: int(time.time()))
    processed_at: Optional[int] = None

    @property
    def processed(self) -> bool:
        return self.processed_at is not None
