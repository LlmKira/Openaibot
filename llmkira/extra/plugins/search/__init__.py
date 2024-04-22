# -*- coding: utf-8 -*-
from typing import Union, Type, List

from pydantic import ConfigDict

__package__name__ = "llmkira.extra.plugins.search"
__plugin_name__ = "search_in_google"
__openapi_version__ = "20240416"

from llmkira.sdk.tools import verify_openapi_version  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

verify_openapi_version(__package__name__, __openapi_version__)  # noqa: E402
from llmkira.openai.cell import Tool, ToolCall, class_tool  # noqa: E402
from llmkira.openapi.fuse import resign_plugin_executor  # noqa: E402
from llmkira.sdk.tools import PluginMetadata  # noqa: E402
from llmkira.sdk.tools.schema import FuncPair, BaseTool  # noqa: E402
from llmkira.task import Task, TaskHeader  # noqa: E402
from llmkira.task.schema import Location, ToolResponse, EventMessage  # noqa: E402
from .engine import SerperSearchEngine, build_search_tips, search_in_duckduckgo  # noqa: E402


class Search(BaseModel):
    keywords: str = Field(description="question entered in the search website")
    model_config = ConfigDict(extra="allow")


@resign_plugin_executor(tool=Search)
async def search_on_serper(search_sentence: str, api_key: str = None):
    if not api_key:
        return search_in_duckduckgo(search_sentence)
    result = await SerperSearchEngine(api_key=api_key).search(search_sentence)
    return build_search_tips(search_items=result)


class SearchTool(BaseTool):
    """
    搜索工具
    """

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = Search
    keywords: list = [
        "怎么",
        "Where",
        "Search",
        "search",
        "How to",
        "为什么",
        "how to",
        "news",
        "新闻",
        "解释",
        "怎样的",
        "请教",
        "介绍",
        "搜索",
    ]
    env_required: List[str] = ["API_KEY"]
    env_prefix: str = "SERPER_"

    def require_auth(self, env_map: dict) -> bool:
        if env_map.get("SERPER_API_KEY", None) is None:
            return True
        return False

    @classmethod
    def env_help_docs(cls, empty_env: List[str]) -> str:
        """
        Provide help message for environment variables
        :param empty_env: The environment variable list that not configured
        :return: The help message
        """
        message = ""
        if "SERPER_API_KEY" in empty_env:
            message += (
                "You need to configure https://serper.dev/ to start use this tool"
            )
        return message

    def func_message(self, message_text, message_raw, address, **kwargs):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        if message_text.endswith("?"):
            return self.function
        if message_text.endswith("？"):
            return self.function
        # 正则匹配
        if self.pattern:
            match = self.pattern.match(message_text)
            if match:
                return self.function
        return None

    async def failed(
        self,
        task: "TaskHeader",
        receiver: "Location",
        exception,
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
        **kwargs,
    ):
        meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Run Failed {exception}",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )
        await Task.create_and_send(
            queue_name=receiver.platform,
            task=TaskHeader(
                sender=task.sender,
                receiver=receiver,
                task_sign=meta,
                message=[
                    EventMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text=f"🍖{__plugin_name__} Run Failed：{exception},report it to user.",
                    )
                ],
            ),
        )

    async def callback(
        self,
        task: "TaskHeader",
        receiver: "Location",
        env: dict,
        arg: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
        **kwargs,
    ):
        return True

    async def run(
        self,
        task: "TaskHeader",
        receiver: "Location",
        arg: dict,
        env: dict,
        pending_task: "ToolCall",
        refer_llm_result: dict = None,
    ):
        """
        处理message，返回message
        """

        _set = Search.model_validate(arg)
        _search_result = await search_on_serper(
            search_sentence=_set.keywords,
            api_key=env.get("SERPER_API_KEY", None),
        )
        # META
        _meta = task.task_sign.reprocess(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"SearchData: {_search_result},Please give reference link when use it.",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )
        await Task.create_and_send(
            queue_name=receiver.platform,
            task=TaskHeader(
                sender=task.sender,  # 继承发送者
                receiver=receiver,  # 因为可能有转发，所以可以单配
                task_sign=_meta,
                message=[],
            ),
        )


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Search fact on google.com",
    usage="以问号结尾的句子即可触发",
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(Search), tool=SearchTool)},
)
