# -*- coding: utf-8 -*-
from pydantic import ConfigDict

__package__name__ = "llmkira.extra.plugins.finish"
__plugin_name__ = "finish_conversation"
__openapi_version__ = "20231111"

from llmkira.sdk.func_calling import verify_openapi_version
from llmkira.sdk.schema import Function

verify_openapi_version(__package__name__, __openapi_version__)

from pydantic import BaseModel, Field

from llmkira.schema import RawMessage
from llmkira.sdk.func_calling import BaseTool, PluginMetadata
from llmkira.sdk.func_calling.schema import FuncPair
from llmkira.task import Task, TaskHeader
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llmkira.sdk.schema import TaskBatch
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
    comment: str = Field(default=":)", description="end with a question or a comment.(__language: $context)")
    model_config = ConfigDict(extra="allow")


class FinishTool(BaseTool):
    """
    搜索工具
    """
    silent: bool = True
    function: Function = finish
    deploy_child: int = 0
    """可部署子任务 0，终结任务链"""

    def pre_check(self):
        return True

    def func_message(self, message_text, **kwargs):
        # 一直返回，永远处理
        return self.function

    async def failed(self,
                     task: "TaskHeader", receiver: "TaskHeader.Location",
                     env: dict,
                     exception,
                     arg: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                     **kwargs
                     ):
        _meta = task.task_meta.reply_notify(
            plugin_name=__plugin_name__,
            callback=TaskHeader.Meta.Callback.create(
                function_response=f"Run Failed {exception}",
                name=__plugin_name__,
                tool_call_id=pending_task.get_batch_id()
            ),
            write_back=True,
            release_chain=True
        )
        await Task(queue=receiver.platform).send_task(
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_meta=_meta,
                message=[
                    RawMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"🍖{__plugin_name__} Run Failed：{exception}"
                    )
                ]
            )
        )

    async def callback(self,
                       task: "TaskHeader", receiver: "TaskHeader.Location",
                       env: dict,
                       arg: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                       **kwargs
                       ):
        return True

    async def run(self,
                  task: "TaskHeader", receiver: "TaskHeader.Location",
                  arg: dict, env: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                  ):
        """
        处理message，返回message
        """
        _set = Finish.model_validate(arg)
        # META
        _meta = task.task_meta.reply_message(
            plugin_name=__plugin_name__,
            callback=[
                TaskHeader.Meta.Callback.create(
                    name=__plugin_name__,
                    function_response="Finished the conversation",
                    tool_call_id=pending_task.get_batch_id()
                )
            ],
            function_enable=False
        )
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


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Finish the conversation",
    usage="all matched",
    openapi_version=__openapi_version__,
    function={
        FuncPair(function=finish, tool=FinishTool)
    },
)
