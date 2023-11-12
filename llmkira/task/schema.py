# -*- coding: utf-8 -*-
# @Time    : 2023/10/14 下午2:16
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import time
from typing import TYPE_CHECKING, Dict, Any
from typing import Tuple, List, Union, Optional

import hikari
import khl
import orjson
from dotenv import load_dotenv
from loguru import logger
from pydantic import model_validator, ConfigDict, Field, BaseModel, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict
from telebot import types

from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.schema import LlmResult
from llmkira.sdk.schema import File, Function, ToolMessage, FunctionMessage, TaskBatch
from llmkira.sdk.utils import sync

if TYPE_CHECKING:
    from llmkira.sender.slack.schema import SlackMessageEvent


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class RabbitMQ(BaseSettings):
    """
    代理设置
    """
    amqp_dsn: str = Field("amqp://admin:8a8a8a@localhost:5672", validation_alias='AMQP_DSN')
    _verify_status: bool = PrivateAttr(default=False)
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra="ignore")

    @model_validator(mode='after')
    def is_connect(self):
        import aio_pika
        try:
            sync(aio_pika.connect_robust(
                self.amqp_dsn
            ))
        except Exception as e:
            self._verify_status = False
            logger.error(f'\n⚠️ RabbitMQ DISCONNECT, pls set AMQP_DSN in .env\n--error {e} --dsn {self.amqp_dsn}')
        else:
            self._verify_status = True
            logger.success(f"RabbitMQ connect success")
            if self.amqp_dsn == "amqp://admin:8a8a8a@localhost:5672":
                logger.warning(f"\n⚠️ You are using the default RabbitMQ password")
        return self

    @property
    def available(self):
        return self._verify_status

    @property
    def task_server(self):
        return self.amqp_dsn


load_dotenv()
RabbitMQSetting = RabbitMQ()


class TaskHeader(BaseModel):
    """
    任务链节点
    """
    model_config = ConfigDict()

    class Meta(BaseModel):
        class Callback(BaseModel):
            function_response: str = Field("empty response", description="工具响应内容")
            name: str = Field(None, description="功能名称", pattern=r"^[a-zA-Z0-9_]+$")
            tool_call_id: Optional[str] = Field(None, description="工具调用ID")

            @model_validator(mode="after")
            def check(self):
                """
                检查回写消息
                """
                if not self.tool_call_id and not self.name:
                    raise ValueError("tool_call_id or name must be set")
                return self

            @classmethod
            def create(cls,
                       *,
                       function_response: str,
                       name: str,
                       tool_call_id: Union[str, None] = None
                       ):
                return cls(
                    function_response=function_response,
                    name=name,
                    tool_call_id=tool_call_id,
                )

            def get_tool_message(self) -> Union[ToolMessage]:
                if self.tool_call_id:
                    return ToolMessage(
                        tool_call_id=self.tool_call_id,
                        content=self.function_response
                    )
                raise ValueError("tool_call_id is empty")

            def get_function_message(self) -> Union[FunctionMessage]:
                if self.name:
                    return FunctionMessage(
                        name=self.name,
                        content=self.function_response
                    )
                raise ValueError("name is empty")

        """当前链条的层级"""
        sign_as: Tuple[int, str, str] = Field((0, "root", "default"), description="签名")

        """函数并行的信息"""
        plan_chain_archive: List[Tuple[TaskBatch, Union[Exception, dict, str]]] = Field(
            default=[],
            description="完成的节点"
        )
        plan_chain_pending: List[TaskBatch] = Field(default=[], description="待完成的节点")
        plan_chain_length: int = Field(default=0, description="节点长度")
        plan_chain_complete: Optional[bool] = Field(False, description="是否完成此集群")

        """功能状态与缓存"""
        function_enable: bool = Field(False, description="功能开关")
        function_list: List[Function] = Field([], description="功能列表")
        function_salvation_list: List[Function] = Field([], description="上回合的功能列表，用于容错")

        """携带插件的写回结果"""
        write_back: bool = Field(False, description="写回消息")
        callback: List[Callback] = Field(
            default=[],
            description="用于回写，插件返回的消息头，标识 function 的名字"
        )

        """接收器的路由规则"""
        callback_forward: bool = Field(False, description="转发消息")
        callback_forward_reprocess: bool = Field(False, description="转发消息，但是要求再次处理")
        direct_reply: bool = Field(False, description="直接回复,跳过函数处理等")

        release_chain: bool = Field(False, description="是否响应队列中的函数集群拉起请求")
        """部署点的生长规则"""
        resign_next_step: bool = Field(True, description="函数集群是否可以继续拉起其他函数集群")
        run_step_already: int = Field(0, description="函数集群计数器")
        run_step_limit: int = Field(4, description="函数集群计数器上限")

        """函数中枢的依赖变量"""
        verify_uuid: Optional[str] = Field(None, description="认证链的UUID，根据此UUID和 Map 可以确定哪个需要执行")
        verify_map: Dict[str, TaskBatch] = Field({},
                                                 description="函数节点的认证信息，经携带认证重发后可通过")
        llm_result: Any = Field(None, description="存储任务的衍生信息源")
        llm_type: Optional[str] = Field(None, description="存储任务的衍生信息源类型")
        extra_args: dict = Field({}, description="提供额外参数")

        @model_validator(mode="after")
        def check(self):
            if isinstance(self.llm_result, dict):
                if not self.llm_result.get("model"):
                    raise TypeError("Invalid llm_result")

            if not any([self.callback_forward, self.callback_forward_reprocess, self.direct_reply]):
                if self.write_back:
                    logger.warning("you shouldn*t write back without callback_forward or direct_reply")
                    self.write_back = False
            # If it is the root node, it cannot be written back.
            # Because the message posted by the user is always the root node.
            # Writing back will cause duplicate messages.
            # Because the middleware will write the message back
            if self.sign_as[0] == 0 and self.write_back:
                logger.warning("root node shouldn*t write back")
                self.write_back = False
            return self

        @classmethod
        def from_root(cls, release_chain, function_enable, platform: str = "default", **kwargs):
            return cls(
                sign_as=(0, "root", platform),
                release_chain=release_chain,
                function_enable=function_enable,
                **kwargs
            )

        def pack_loop(
                self,
                *,
                plan_chain_pending: List[TaskBatch],
                verify_map: dict,
        ) -> "TaskHeader.Meta":
            """
            打包循环信息
            :return: Meta
            """
            if not verify_map:
                verify_map = self.verify_map
            if not plan_chain_pending:
                raise ValueError("plan_chain_pending can't be empty")
            _new = self.model_copy(deep=True)
            _new.plan_chain_pending = plan_chain_pending
            _new.plan_chain_length = len(plan_chain_pending)
            _new.verify_map = verify_map
            return _new

        async def work_pending_task(self,
                                    verify_uuid: str
                                    ) -> Optional[TaskBatch]:
            """
            获取待完成的节点
            如果有 uuid 则优先在 map 里面获取对应的节点名称，根据名称查找pending.
            执行完成后，将节点移动到 archive
            """
            if not self.plan_chain_pending:
                self.plan_chain_complete = True
                return logger.trace("no pending task")
            if verify_uuid:
                _task_batch = self.verify_map.get(verify_uuid, None)
                if _task_batch:
                    return _task_batch
            return self.plan_chain_pending[0]

        async def complete_task(self,
                                task_batch: TaskBatch,
                                run_result: Union[Exception, dict, str]
                                ) -> "TaskHeader.Meta":
            """
            完成此集群
            :return: Meta
            """
            self.plan_chain_archive.append((task_batch, run_result))
            self.plan_chain_pending.remove(task_batch)
            if not self.plan_chain_pending:
                self.plan_chain_complete = True
            return self

        def get_verify_uuid(self, task_batch: TaskBatch) -> Optional[str]:
            """
            从 Map 获取验证UUID
            """
            for key, item in self.verify_map.items():
                if item == task_batch:
                    return key
            return None

        @property
        def is_complete(self) -> bool:
            """
            完成状态
            :return: Meta
            """
            return self.plan_chain_complete

        model_config = ConfigDict(extra="ignore",
                                  arbitrary_types_allowed=True
                                  )

        def child(self, name) -> "TaskHeader.Meta":
            """
            生成副本，仅仅是子节点，继承父节点的功能
            """
            self.sign_as = (self.sign_as[0] + 1, "child", name)
            self.run_step_already += 1
            return self.model_copy(deep=True)

        def chain(self,
                  name,
                  write_back: bool,
                  release_chain: bool
                  ) -> "TaskHeader.Meta":
            """
            生成副本，重置链条
            """
            self.sign_as = (self.sign_as[0] + 1, "chain", name)
            self.run_step_already += 1
            self.callback_forward = False
            self.callback_forward_reprocess = False
            self.direct_reply = False
            self.write_back = write_back
            self.release_chain = release_chain
            return self.model_copy(deep=True)

        def reply_direct(self,
                         *,
                         chain_name: str,
                         ):
            """
            决定路由规则。只通知，不重组函数和初始化任何东西。
            最稳定的回复方式，不会出现任何问题，但是不会有任何功能。
            回复消息,其他什么都不做！
            """
            _child = self.child(chain_name)
            _child.callback_forward = False
            _child.callback_forward_reprocess = False
            _child.direct_reply = True
            _child.write_back = False
            _child.release_chain = False
            _child.function_enable = False
            return _child

        def reply_notify(self,
                         *,
                         plugin_name: str,
                         callback: List[Callback],
                         release_chain: bool,
                         function_enable: bool = False,
                         write_back: bool = None
                         ):
            """
            决定路由规则
            默认回复消息，其他参数自由
            :param plugin_name: 插件名称
            :param callback: 元信息
            :param write_back: 是否写回，写回此通知到消息历史,比如插件运行失败了，要不要写回消息历史让AI看到呢
            :param release_chain: 是否释放任务链，是否释放任务链，比如插件运行失败，错误消息发送的同时需要释放任务链防止挖坟
            :param function_enable: 是否开启功能
            :return: Meta
            """
            assert isinstance(callback, list), "callback must be list"
            _child = self.child(plugin_name)
            _child.callback = callback
            _child.callback_forward = True
            _child.callback_forward_reprocess = False
            _child.direct_reply = False
            _child.write_back = write_back
            _child.release_chain = release_chain
            _child.function_enable = function_enable
            return _child

        def reply_raw(self,
                      *,
                      plugin_name: str,
                      callback: List[Callback],
                      function_enable: bool = True
                      ):
            """
            决定路由规则
            回写消息，释放任务链，要求再次处理，回复消息
            :param plugin_name: 插件名称
            :param callback: 元信息
            :param function_enable: 是否允许机器人用函数再次处理
            """
            assert isinstance(callback, list), "callback must be list"
            _child = self.child(plugin_name)
            _child.callback = callback
            _child.callback_forward = True
            _child.callback_forward_reprocess = True
            _child.direct_reply = False
            _child.write_back = True
            _child.release_chain = True
            _child.function_enable = function_enable
            return _child

        def reply_message(self,
                          *,
                          plugin_name: str,
                          callback: List[Callback],
                          function_enable: bool = True
                          ):
            """
            决定路由规则
            回写消息，释放任务链，回复消息
            :param plugin_name: 插件名称
            :param callback: 元信息
            :param function_enable: 是否允许机器人用函数再次处理
            """
            assert isinstance(callback, list), "callback must be list"
            _child = self.child(plugin_name)
            _child.callback = callback
            _child.callback_forward = True
            _child.callback_forward_reprocess = False
            _child.direct_reply = False
            _child.write_back = True
            _child.release_chain = True
            _child.function_enable = function_enable
            return _child

    class Location(BaseModel):
        """
        Union[str, int]
        here .... address
        """
        platform: str = Field(None, description="platform")
        user_id: Union[str, int] = Field(None, description="user id")
        chat_id: Union[str, int] = Field(None, description="guild id(channel in dm)/Telegram chat id")
        thread_id: Optional[Union[str, int]] = Field(None, description="channel id/Telegram thread")
        message_id: Optional[Union[str, int]] = Field(None, description="message id")

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

    task_meta: Meta = Field(Meta(), description="任务元数据")
    sender: Location = Field(..., description="发信人")
    receiver: Location = Field(..., description="接收人")
    message: List[RawMessage] = Field(None, description="消息内容")

    @classmethod
    def from_telegram(cls,
                      message: Union[types.Message],
                      task_meta: Meta,
                      file: List[File] = None,
                      reply: bool = True,
                      hide_file_info: bool = False,
                      deliver_back_message: List[types.Message] = None,
                      trace_back_message: List[types.Message] = None
                      ):
        """
        从telegram消息中构建任务
        """

        # none -> []
        trace_back_message = [] if not trace_back_message else trace_back_message
        file = [] if not file else file
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: types.Message) -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if isinstance(_message, types.Message):
                user_id = _message.from_user.id
                chat_id = _message.chat.id
                text = _message.text if _message.text else _message.caption
                created_at = _message.date
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                text=text if text else f"(empty message)",
                created_at=str(created_at)
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]

        # A
        _file_name = []
        for _file in file:
            _file_name.append(_file.file_prompt)
        # 转换为标准消息
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        # 附加文件信息
        head_message.file = file
        # 追加元信息
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)

        # 追加回溯消息
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                if item:
                    message_list.append(_convert(item))
        message_list.extend(deliver_message_list)
        message_list.append(head_message)

        # 去掉 None
        message_list = [item for item in message_list if item]

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="telegram",
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                # dm=message.chat.type == "private",
                message_id=message.message_id if reply else None
            ),
            receiver=cls.Location(
                platform="telegram",
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                message_id=message.message_id if reply else None
            ),
            message=message_list
        )

    @classmethod
    def from_function(cls,
                      llm_result: LlmResult,
                      task_meta: Meta,
                      receiver: Location,
                      message: List[RawMessage] = None
                      ):
        """
        从 Openai LLM Task中构建任务
        """
        # task_meta = task_meta.child("function") 发送到 function 的消息不需加点，因为此时 接收器算发送者
        task_meta.llm_result = llm_result
        task_meta.llm_type = llm_result.__repr_name__()
        return cls(
            task_meta=task_meta,
            sender=receiver,
            receiver=receiver,
            message=message
        )

    @classmethod
    def from_router(cls, from_, to_, user_id, method, message_text):
        _meta_arg = {}
        if method == "task":
            _meta_arg["function_enable"] = True
        elif method == "push":
            _meta_arg["callback_forward"] = True
        elif method == "chat":
            _meta_arg["function_enable"] = False
        task_meta = cls.Meta(
            **_meta_arg
        )

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform=from_,
                chat_id=user_id,
                user_id=user_id,
                message_id=None
            ),
            receiver=cls.Location(
                platform=to_,
                chat_id=user_id,
                user_id=user_id,
                message_id=None
            ),
            message=[
                RawMessage(
                    user_id=user_id,
                    chat_id=user_id,
                    text=message_text,
                    created_at=str(int(time.time()))
                )
            ]
        )

    @classmethod
    def from_discord_hikari(cls,
                            message: hikari.Message,
                            task_meta: Meta,
                            file: List[File] = None,
                            reply: bool = True,
                            hide_file_info: bool = False,
                            deliver_back_message: List[hikari.Message] = None,
                            trace_back_message: List[hikari.Message] = None
                            ):
        # none -> []
        trace_back_message = [] if not trace_back_message else trace_back_message
        file = [] if not file else file
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: hikari.Message) -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if isinstance(_message, hikari.Message):
                user_id = message.author.id
                chat_id = message.guild_id if message.guild_id else message.channel_id
                thread_id = message.channel_id
                text = _message.content
                created_at = _message.created_at.timestamp()
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                thread_id=thread_id,
                text=text if text else f"(empty message)",
                created_at=str(created_at)
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]

        # A
        _file_name = []
        for _file in file:
            _file_name.append(_file.file_prompt)
        # 转换为标准消息
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        # 附加文件信息
        head_message.file = file
        # 追加元信息
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)

        # 追加回溯消息
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                if item:
                    message_list.append(_convert(item))
        message_list.extend(deliver_message_list)
        message_list.append(head_message)

        # 去掉 None
        message_list = [item for item in message_list if item]

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="discord_hikari",
                thread_id=message.channel_id,
                chat_id=message.guild_id if message.guild_id else message.channel_id,
                user_id=message.author.id,
                message_id=message.id if reply else None
            ),
            receiver=cls.Location(
                platform="discord_hikari",
                thread_id=message.channel_id,
                chat_id=message.guild_id if message.guild_id else message.channel_id,
                user_id=message.author.id,
                message_id=message.id if reply else None
            ),
            message=message_list
        )

    @classmethod
    def from_kook(cls,
                  message: khl.Message,
                  deliver_back_message: List[khl.Message],
                  trace_back_message: List[khl.Message],
                  task_meta: Meta,
                  hide_file_info: bool = False,
                  file: List[File] = None,
                  reply: bool = True,
                  ):
        # none -> []
        trace_back_message = [] if not trace_back_message else trace_back_message
        file = [] if not file else file
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: khl.Message) -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if isinstance(_message, khl.Message):
                user_id = message.author_id
                chat_id = message.ctx.guild.id if message.ctx.guild else message.ctx.channel.id
                thread_id = message.ctx.channel.id
                text = _message.content
                created_at = _message.msg_timestamp
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                thread_id=thread_id,
                text=text if text else f"(empty message)",
                created_at=str(created_at)
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]

        # A
        _file_name = []
        for _file in file:
            _file_name.append(_file.file_prompt)
        # 转换为标准消息
        head_message = _convert(message)
        assert head_message, "HeadMessage is empty"
        # 附加文件信息
        head_message.file = file
        # 追加元信息
        if not hide_file_info:
            head_message.text += "\n" + "\n".join(_file_name)

        # 追加回溯消息
        message_list = []
        if trace_back_message:
            for item in trace_back_message:
                if item:
                    message_list.append(_convert(item))
        message_list.extend(deliver_message_list)
        message_list.append(head_message)

        # 去掉 None
        message_list = [item for item in message_list if item]

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="kook",
                thread_id=message.ctx.channel.id,
                chat_id=message.ctx.guild.id if message.ctx.guild else message.ctx.channel.id,
                user_id=message.author_id,
                message_id=message.id if reply else None
            ),
            receiver=cls.Location(
                platform="kook",
                thread_id=message.ctx.channel.id,
                chat_id=message.ctx.guild.id if message.ctx.guild else message.ctx.channel.id,
                user_id=message.author_id,
                message_id=message.id if reply else None
            ),
            message=message_list
        )

    @classmethod
    def from_slack(cls,
                   message: "SlackMessageEvent",
                   deliver_back_message,
                   task_meta: Meta,
                   hide_file_info: bool = False,
                   file: List[File] = None,
                   reply: bool = True,
                   ):
        """
        https://api.slack.com/methods
        """
        # none -> []
        deliver_back_message = [] if not deliver_back_message else deliver_back_message

        def _convert(_message: "SlackMessageEvent") -> Optional[RawMessage]:
            """
            消息标准化
            """
            if not _message:
                raise ValueError(f"Message is empty")
            if _message.__repr_name__() == "SlackMessageEvent":
                user_id = message.user
                chat_id = message.channel
                thread_id = message.channel
                text = _message.text
                created_at = message.event_ts
            else:
                raise ValueError(f"Unknown message type {type(_message)}")
            return RawMessage(
                user_id=user_id,
                chat_id=chat_id,
                thread_id=thread_id,
                text=text if text else f"(empty message)",
                created_at=str(created_at)
            )

        deliver_message_list: List[RawMessage] = [_convert(msg) for msg in deliver_back_message]
        # A
        _file_prompt = []
        for _file in file:
            _file_prompt.append(_file.file_prompt)
        # 转换为标准消息
        now_message = _convert(message)
        assert now_message, "HeadMessage is empty"
        # 附加文件信息
        now_message.file = file
        # 追加文件元信息
        if not hide_file_info:
            now_message.text += "\n" + "\n".join(_file_prompt)

        message_list = []
        message_list.extend(deliver_message_list)
        message_list.append(now_message)
        # 去掉 None
        message_list = [item for item in message_list if item]

        return cls(
            task_meta=task_meta,
            sender=cls.Location(
                platform="slack",
                thread_id=message.channel,
                chat_id=message.channel,
                user_id=message.user,
                message_id=message.thread_ts if reply else None
            ),
            receiver=cls.Location(
                platform="slack",
                thread_id=message.channel,
                chat_id=message.channel,
                user_id=message.user,
                message_id=message.thread_ts if reply else None
            ),
            message=message_list
        )
