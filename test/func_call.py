# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 下午6:56
# @Author  : sudoskys
# @File    : func_call.py
# @Software: PyCharm


from llmkira.sdk import Function

from llmkira.sdk.func_calling.register import listener
from llmkira.sdk import BaseTool

search = Function(name="get_current_weather", description="Get the current weather")
search.add_property(
    property_name="location",
    property_description="The city and state, e.g. San Francisco, CA",
    property_type="string",
    required=True
)


@listener(function=search)
class SearchTool(BaseTool):
    """
    搜索工具
    """
    function: Function = search

    def func_message(self, message_text):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        if "搜索" in message_text:
            return self.function
        else:
            return None

    async def __call__(self, *args, **kwargs):
        """
        处理message，返回message
        """
        return "搜索成功"
