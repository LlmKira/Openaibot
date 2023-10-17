# -*- coding: utf-8 -*-
__plugin_name__ = "translate_file"
__openapi_version__ = "20231017"

from llmkira.sdk.func_calling import verify_openapi_version

verify_openapi_version(__plugin_name__, __openapi_version__)
import asyncio
import os
from io import BytesIO
from typing import List

from loguru import logger
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_fixed

from llmkira.middleware.user import UserInfo, SubManager
from llmkira.schema import RawMessage
from llmkira.sdk.endpoint import openai
from llmkira.sdk.endpoint.openai import Function
from llmkira.sdk.func_calling import BaseTool, PluginMetadata
from llmkira.sdk.func_calling.schema import FuncPair
from llmkira.sdk.schema import Message, File
from llmkira.task import Task, TaskHeader

translate = Function(name=__plugin_name__, description="Help user translate [ReadableFile],only support txt/md")
translate.add_property(
    property_name="language",
    property_description="What language should the text be translated into?",
    property_type="string",
    required=True
)
translate.add_property(
    property_name="file_id",
    property_description="regex: file_id=([a-z0-9]{8}), require ReadableFile[...]",
    property_type="string",
    required=True
)


class Translate(BaseModel):
    language: str
    file_id: str

    class Config:
        extra = "allow"


class TranslateTool(BaseTool):
    """
    搜索工具
    """
    function: Function = translate
    keywords: list = ["translate", "转换", "convert", "翻译", "译", "md", 'txt']

    def pre_check(self):
        try:
            import nltk
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            from unstructured.partition.auto import partition
        except Exception as e:
            logger.error(f"plugin:translate_doc:{e},pls check !pip install unstructured")
            return False
        return True

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

    async def failed(self, platform: str, task: TaskHeader, receiver: TaskHeader.Location, reason: str):
        try:
            await Task(queue=platform).send_task(
                task=TaskHeader(
                    sender=task.sender,
                    receiver=receiver,
                    task_meta=TaskHeader.Meta(
                        callback_forward=True,
                        callback=TaskHeader.Meta.Callback(
                            role="function",
                            name=__plugin_name__
                        ),
                    ),
                    message=[
                        RawMessage(
                            user_id=receiver.user_id,
                            chat_id=receiver.chat_id,
                            text="🍖 操作失败，原因：{}".format(reason)
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(e)

    @staticmethod
    @retry(stop=(stop_after_attempt(3) | stop_after_delay(10)), wait=wait_fixed(2), reraise=True)
    async def llm_task(task: TaskHeader, task_desc: str, raw_data: str):
        logger.info("translate_doc:llm_task:{}".format(task_desc))
        _submanager = SubManager(user_id=f"{task.sender.platform}:{task.sender.user_id}")
        driver = _submanager.llm_driver  # 由发送人承担接受者的成本
        model_name = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo-0613")
        endpoint = openai.Openai(
            config=driver,
            model=model_name,
            temperature=0.1,
            messages=Message.create_short_task(
                task_desc=task_desc,
                refer=raw_data,
            ),
        )
        # 调用Openai
        result = await endpoint.create()
        await _submanager.add_cost(
            cost=UserInfo.Cost(token_usage=result.usage.total_tokens, token_uuid=driver.uuid, model_name=model_name)
        )
        assert result.default_message.content, "llm_task.py:llm_task:content is None"
        return result.default_message.content

    async def translate_docs(self, task: TaskHeader, file: File.Data, target_lang: str):
        if not file.file_name.endswith(('md', "txt")):
            raise ValueError("That Type File is Not supported :-(")

        from unstructured.partition.auto import partition
        elements = partition(file=BytesIO(initial_bytes=file.file_data), include_page_breaks=True)
        write_out_name = f"translated_{file.file_name}"

        write_out_file = BytesIO()
        write_out_file.name = write_out_name
        write_out_list = []

        async def _fill_box(text):
            try:
                await asyncio.sleep(2)
                result = await self.llm_task(task=task, task_desc=f"Translate text to {target_lang},as origin format",
                                             raw_data=text)
            except Exception as e:
                logger.error(e)
                result = str(element)
            write_out_list.append(result)

        _buffer = []
        for element in elements:
            _buffer.append(str(element))
            if len("/n".join(_buffer)) >= 1000:
                await _fill_box(text="\n".join(_buffer))
                _buffer = []
        if _buffer:
            await _fill_box(text="\n".join(_buffer))
            _buffer = []

        write_out_file.write("\n\n".join(write_out_list).encode("utf-8"))
        write_out_file.seek(0)
        return write_out_file

    async def callback(self, sign: str, task: TaskHeader):
        return None

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _translate_file = []
            for item in task.message:
                if item.file:
                    for i in item.file:
                        _translate_file.append(i)
            try:
                translate_arg = Translate.parse_obj(arg)
            except Exception:
                raise ValueError("Please specify the following parameters clearly\n file_id=xxx,language=xxx")
            _file_obj = [await RawMessage.download_file(file_id=i.file_id)
                         for i in sorted(set(_translate_file), key=_translate_file.index)]
            _file_obj: List[File.Data] = [item for item in _file_obj if item]

            # 处理文件
            _result: List[File] = []
            if not _file_obj:
                return None
            for item in _file_obj:
                translated_file = await self.translate_docs(task=task, file=item, target_lang=translate_arg.language)
                file_obj = await RawMessage.upload_file(name=translated_file.name, data=translated_file.getvalue())
                _result.append(file_obj)
            # META
            _meta = task.task_meta.child(__plugin_name__)
            _meta.callback_forward = True
            _meta.callback_forward_reprocess = False
            _meta.callback = TaskHeader.Meta.Callback(
                role="function",
                name=__plugin_name__
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
                            file=_result,
                            text="🍖 操作成功！"
                        )
                    ]
                )
            )

            logger.debug("Plugin:translate_doc say: {}".format(translate_arg))
        except Exception as e:
            logger.exception(e)
            await self.failed(platform=receiver.platform, task=task, receiver=receiver, reason=str(e))


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Translate readable file to target language",
    usage=str(TranslateTool().keywords),
    openapi_version=__openapi_version__,
    function={
        FuncPair(function=translate, tool=TranslateTool)
    },
)
