# -*- coding: utf-8 -*-
# @Time    : 2023/11/13 下午6:27
# @Author  : sudoskys
# @File    : pydantic_debug.py
# @Software: PyCharm
from typing import Union, Optional, List, Tuple, Dict, Any

from pydantic import model_validator, Field, BaseModel, ConfigDict

from llmkira.sdk.schema import ToolMessage, FunctionMessage, TaskBatch, Function


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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def chain(self,
              name,
              write_back: bool,
              release_chain: bool
              ) -> "Meta":
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


someUnexpectedType = ...
Meta(
    sign_as=(0, "root", "test"),
    release_chain=True,
    function_enable=True,
    llm_result=someUnexpectedType,
).chain("test", True, True)
