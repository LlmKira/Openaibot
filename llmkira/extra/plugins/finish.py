# -*- coding: utf-8 -*-
__plugin_name__ = "finish_conversation"
__openapi_version__ = "20231017"

from llmkira.sdk.func_calling import verify_openapi_version

verify_openapi_version(__plugin_name__, __openapi_version__)

from typing import Optional

from loguru import logger
from pydantic import BaseModel

from llmkira.schema import RawMessage
from llmkira.sdk.endpoint.openai import Function
from llmkira.sdk.func_calling import BaseTool, PluginMetadata
from llmkira.sdk.func_calling.schema import FuncPair
from llmkira.task import Task, TaskHeader

finish = Function(
    name=__plugin_name__,
    description="The user's question has been fully answered and there is nothing more to add"
)
finish.add_property(
    property_name="comment",
    property_description="end with a question or a comment.(__language: $context)",
    property_type="string"
)


class Finish(BaseModel):
    comment: Optional[str] = None

    class Config:
        extra = "allow"


class FinishTool(BaseTool):
    """
    搜索工具
    """
    silent: bool = True
    function: Function = finish
    deploy_child: int = 0

    def pre_check(self):
        return True

    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        return self.function

    async def failed(self, platform, task, receiver, reason):
        try:
            _meta = task.task_meta.child(__plugin_name__)
            _meta.direct_reply = True
            _meta.callback_forward = False
            _meta.callback_forward_reprocess = False
            _meta.callback = TaskHeader.Meta.Callback(
                role="function",
                name=__plugin_name__
            )
            await Task(queue=platform).send_task(
                task=TaskHeader(
                    sender=task.sender,
                    receiver=receiver,
                    task_meta=_meta,
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text=f"🍖 {__plugin_name__}操作失败了！原因：{reason}"
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(e)

    async def callback(self, sign: str, task: TaskHeader):
        return True

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _set = Finish.parse_obj(arg)
            # META
            _meta = task.task_meta.child(__plugin_name__)
            _meta.callback_forward = True
            _meta.callback_forward_reprocess = False
            _meta.callback = TaskHeader.Meta.Callback(
                role="function",
                name=__plugin_name__
            )
            if _set.comment:
                await Task(queue=receiver.platform).send_task(
                    task=TaskHeader(
                        sender=task.sender,  # 继承发送者
                        receiver=receiver,  # 因为可能有转发，所以可以单配
                        task_meta=_meta,
                        message=[
                            RawMessage(
                                user_id=receiver.user_id,
                                chat_id=receiver.chat_id,
                                text=_set.comment
                            )
                        ]
                    )
                )
        except Exception as e:
            await self.failed(platform=receiver.platform, task=task, receiver=receiver, reason="Failed to execute!")
            logger.exception(e)


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Finish the conversation",
    usage="all matched",
    openapi_version=__openapi_version__,
    function={
        FuncPair(function=finish, tool=FinishTool)
    },
)
