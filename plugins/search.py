# -*- coding: utf-8 -*-
# @Time    : 2023/8/24 下午11:22
# @Author  : sudoskys
# @File    : search.py
# @Software: PyCharm

from loguru import logger
from pydantic import BaseModel

from middleware.user import SubManager, UserInfo
from schema import TaskHeader, RawMessage
from sdk.endpoint import openai
from sdk.endpoint.openai import Function
from sdk.func_call import BaseTool, listener
from sdk.schema import Message
from task import Task

__plugin_name__ = "search_in_google"

search = Function(name=__plugin_name__, description="Search/validate uncertain/unknownEvents/Meme fact on google.com")
search.add_property(
    property_name="keywords",
    property_description="question entered in the search website",
    property_type="string",
    required=True
)


def search_on_duckduckgo(search_sentence: str, key_words: str = None):
    from duckduckgo_search import DDGS
    from sdk.filter import Sublimate
    with DDGS(timeout=20) as ddgs:
        _text = []
        for r in ddgs.text(search_sentence):
            _title = r.get("title")
            _href = r.get("href")
            _body = r.get("body")
            _text.append(_body)
    if key_words:
        must_key = [key_words]
    else:
        must_key = None
    _test_result = Sublimate(_text).valuation(match_sentence=search_sentence, match_keywords=must_key)
    _result = []
    for key in _test_result[:4]:
        _result.append(key[0])
        # hidden clues
    return "\nHint Clues:".join(_result)


class Search(BaseModel):
    keywords: str

    class Config:
        extra = "allow"


@listener(function=search)
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
            from sdk.filter import Sublimate
            return True
        except ImportError as e:
            logger.warning(f"plugin:package <duckduckgo_search> not found,please install it first:{e}")
            return False

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

    async def failed(self, platform, task, receiver, reason):
        try:
            await Task(queue=platform).send_task(
                task=TaskHeader(
                    sender=task.sender,
                    receiver=receiver,
                    task_meta=TaskHeader.Meta(callback_forward=True,
                                              callback=TaskHeader.Meta.Callback(
                                                  role="function",
                                                  name=__plugin_name__
                                              ),
                                              ),
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

    @staticmethod
    async def llm_task(task, task_desc, raw_data):
        _submanager = SubManager(user_id=task.sender.user_id)
        driver = _submanager.llm_driver  # 由发送人承担接受者的成本
        model_name = "gpt-3.5-turbo-0613"
        endpoint = openai.Openai(
            config=driver,
            model=model_name,
            messages=Message.create_task_message_list(
                task_desc=task_desc,
                refer=raw_data
            ),
        )
        # 调用Openai
        result = await endpoint.create()
        _message = openai.Openai.parse_single_reply(response=result)
        _usage = openai.Openai.parse_usage(response=result)
        await _submanager.add_cost(
            cost=UserInfo.Cost(token_usage=_usage, token_uuid=driver.uuid, model_name=model_name)
        )
        return _message.content

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _set = Search.parse_obj(arg)
            _search_result = search_on_duckduckgo(_set.keywords)
            _question = task.message[0].text
            await Task(queue=receiver.platform).send_task(
                task=TaskHeader(
                    sender=task.sender,  # 继承发送者
                    receiver=receiver,  # 因为可能有转发，所以可以单配
                    task_meta=TaskHeader.Meta(
                        callback_forward=True,
                        reprocess_needed=True,  # 立刻追加请求
                        callback=TaskHeader.Meta.Callback(
                            role="function",
                            name=__plugin_name__
                        ),
                    ),
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text=_search_result
                        )
                    ]
                )
            )
        except Exception as e:
            logger.exception(e)
            await self.failed(platform=receiver.platform, task=task, receiver=receiver, reason="搜索失败了！")
