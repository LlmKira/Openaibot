# -*- coding: utf-8 -*-
__package__name__ = "llmkira.extra.plugins.search"
__plugin_name__ = "search_in_google"
__openapi_version__ = "20231027"

from llmkira.extra.user import CostControl, UserCost
from llmkira.middleware.llm_provider import GetAuthDriver
from llmkira.sdk import resign_plugin_executor
from llmkira.sdk.func_calling import verify_openapi_version

verify_openapi_version(__package__name__, __openapi_version__)
from loguru import logger
from pydantic import BaseModel

from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.endpoint.openai import Function
from llmkira.sdk.func_calling import BaseTool, PluginMetadata
from llmkira.sdk.func_calling.schema import FuncPair
from llmkira.sdk.schema import Message
from llmkira.task import Task, TaskHeader

search = Function(
    name=__plugin_name__,
    description="Search/validate uncertain/unknownEvents/Meme fact on google.com."
)
search.add_property(
    property_name="keywords",
    property_description="question entered in the search website",
    property_type="string",
    required=True
)


@resign_plugin_executor(function=search)
def search_on_duckduckgo(search_sentence: str, key_words: str = None):
    logger.debug(f"Plugin:search_on_duckduckgo {search_sentence}")
    from duckduckgo_search import DDGS
    from llmkira.sdk.filter import Sublimate
    sort_text = []
    link_refer = {}
    with DDGS(timeout=20) as ddgs:
        search_result = ddgs.text(search_sentence)
        for r in search_result:
            _title = r.get("title")
            _href = r.get("href")
            _body = r.get("body")
            link_refer[_body] = _href
            sort_text.append(_body)
    must_key = [key_words] if key_words else None
    sorted_result = Sublimate(sort_text).valuation(match_sentence=search_sentence, match_keywords=must_key)
    valuable_result = [item[0] for item in sorted_result[:4]]
    # 构建单条内容
    clues = []
    for key, item in enumerate(valuable_result):
        clues.append(
            f"\nPage #{key}\n🔍Contents:{item}\n"
            f"🔗Source:{link_refer.get(item, 'https://google.com/')}\n"
        )
    content = "\n".join(clues)
    return "[🔍SearchPage]\n" + content + (
        "\n[Page End]"
        "\n[ReplyFormat:`$summary_answer \n [$index]($source_link) * num` to mark links]"
    )


class Search(BaseModel):
    keywords: str

    class Config:
        extra = "allow"


class SearchTool(BaseTool):
    """
    搜索工具
    """
    silent: bool = False
    function: Function = search
    keywords: list = [
        "怎么", "How", "件事", "牢大", "作用", "知道", "什么", "认识", "What", "http",
        "what", "who", "how", "Who",
        "Why", "作品", "why", "Where",
        "了解", "简述", "How to", "是谁", "how to",
        "解释", "怎样的", "新闻", "ニュース", "电影", "番剧", "アニメ",
        "2022", "2023", "请教", "介绍",
        "怎样", "吗", "么", "？", "?", "呢",
        "评价", "搜索", "百度", "谷歌", "bing", "谁是", "上网"
    ]

    def pre_check(self):
        try:
            from duckduckgo_search import DDGS
            from llmkira.sdk.filter import Sublimate
            return True
        except ImportError as e:
            logger.warning(f"plugin:package <duckduckgo_search> not found,please install it first:{e}")
            return False

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

    async def failed(self, task: TaskHeader, receiver, arg, exception, **kwargs):
        _meta = task.task_meta.reply_notify(
            plugin_name=__plugin_name__,
            callback=TaskHeader.Meta.Callback(
                role="function",
                name=__plugin_name__
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

    @staticmethod
    async def llm_task(plugin_name, task: TaskHeader, task_desc: str, raw_data: str):
        logger.info("llm_tool:{}".format(task_desc))
        auth_client = GetAuthDriver(uid=task.sender.uid)
        driver = await auth_client.get()
        endpoint = openai.Openai(
            config=driver,
            model=driver.model,
            temperature=0.1,
            messages=Message.create_task_message_list(
                task_desc=task_desc,
                refer=raw_data
            ),
        )
        # 调用Openai
        result = await endpoint.create()
        # 记录消耗
        await CostControl.add_cost(
            cost=UserCost.create_from_function(
                uid=task.sender.uid,
                request_id=result.id,
                cost_by=plugin_name,
                token_usage=result.usage.total_tokens,
                token_uuid=driver.uuid,
                model_name=driver.model
            )
        )
        assert result.default_message.content, "llm_task.py:llm_task:content is None"
        return result.default_message.content

    async def callback(self, task, receiver, arg, result, **kwargs):
        return None

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """

        _set = Search.parse_obj(arg)
        _search_result = search_on_duckduckgo(_set.keywords)
        # META
        _meta = task.task_meta.reply_raw(
            plugin_name=__plugin_name__,
            callback=TaskHeader.Meta.Callback(
                role="function",
                name=__plugin_name__
            )
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
                        text=_search_result
                    )
                ]
            )
        )


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Search/validate uncertain/unknownEvents/Meme fact on google.com",
    usage="search <keywords>",
    openapi_version=__openapi_version__,
    function={
        FuncPair(function=search, tool=SearchTool)
    },
)
