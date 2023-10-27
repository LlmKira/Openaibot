# -*- coding: utf-8 -*-
# @Time    : 2023/10/24 下午8:35
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from typing import List

from ...schema import RawMessage
from ...sdk import get_error_plugin
from ...sdk.func_calling import ToolRegister
from ...sdk.schema import Function
from ...task import TaskHeader


class FunctionReorganize(object):

    def __init__(self, task):
        self.task: TaskHeader = task
        self._functions: List[Function] = []

    async def _ignore(self, error_times):
        """
        忽略错误插件
        """
        for _plugin in get_error_plugin(error_times=error_times):
            if _plugin in self._functions:
                self._functions.remove(_plugin)

    @staticmethod
    async def unique(functions: List[Function] = None):
        _dict = {}
        for function in functions:
            assert isinstance(function, Function), "llm_task.py:function type error,cant unique"
            _dict[function.name] = function
        functions = list(_dict.values())
        return functions

    async def _build(self):
        functions = []
        if self.task.task_meta.function_enable:
            # 继承函数
            functions = self.task.task_meta.function_list
            if self.task.task_meta.sign_as[0] == 0:
                # 复制救赎
                self.task.task_meta.function_salvation_list = self.task.task_meta.function_list
                functions = []
                # 重整
                for _index, _message in enumerate(self.task.message):
                    _message: RawMessage
                    functions.extend(
                        ToolRegister().filter_pair(key_phrases=_message.text, file_list=_message.file)
                    )
                self.task.task_meta.function_list = functions
        if self.task.task_meta.sign_as[0] == 0:
            # 容错一层旧节点
            functions.extend(self.task.task_meta.function_salvation_list)
        self._functions = await self.unique(functions)

    async def build(self) -> List[Function]:
        await self._build()
        self._functions = await self.unique(self._functions)
        # 过滤
        await self._ignore(error_times=10)
        return self._functions
