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
from .engine import SerperSearchEngine, build_search_tips  # noqa: E402


class Search(BaseModel):
    keywords: str = Field(description="question entered in the search website")
    model_config = ConfigDict(extra="allow")


@resign_plugin_executor(tool=Search)
async def search_on_serper(search_sentence: str, api_key: str):
    result = await SerperSearchEngine(api_key=api_key).search(search_sentence)
    return build_search_tips(search_items=result)


class Search(BaseModel):
    keywords: str
    model_config = ConfigDict(extra="allow")


class SearchTool(BaseTool):
    """
    搜索工具
    """

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = Search
    keywords: list = [
        "怎么",
        "How",
        "件事",
        "牢大",
        "作用",
        "知道",
        "什么",
        "认识",
        "What",
        "http",
        "what",
        "who",
        "how",
        "Who",
        "Why",
        "作品",
        "why",
        "Where",
        "了解",
        "简述",
        "How to",
        "是谁",
        "how to",
        "解释",
        "怎样的",
        "新闻",
        "ニュース",
        "电影",
        "番剧",
        "アニメ",
        "2022",
        "2023",
        "请教",
        "介绍",
        "怎样",
        "吗",
        "么",
        "？",
        "?",
        "呢",
        "评价",
        "搜索",
        "百度",
        "谷歌",
        "bing",
        "谁是",
        "上网",
    ]
    env_required: List[str] = ["API_KEY"]
    env_prefix: str = "SERPER_"

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

    def func_message(self, message_text, **kwargs):
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
        meta = task.task_sign.notify(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=f"Run Failed {exception}",
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
            memory_able=True,
            response_snapshot=True,
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
                        text=f"🍖{__plugin_name__} Run Failed：{exception}",
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
        _search_result = search_on_serper(
            search_sentence=_set.keywords,
            api_key=env.get("serper_api_key"),
        )
        # META
        _meta = task.task_sign.reprocess(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=str(_search_result),
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
                message=[
                    EventMessage(
                        user_id=receiver.user_id,
                        chat_id=receiver.chat_id,
                        text="🔍 Searching Done",
                    )
                ],
            ),
        )


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Search fact on google.com",
    usage="以问号结尾的句子即可触发",
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(Search), tool=SearchTool)},
)
