# -*- coding: utf-8 -*-
from pydantic import field_validator, ConfigDict

__package__name__ = "llmkira.extra.plugins.sticker"
__plugin_name__ = "convert_to_sticker"
__openapi_version__ = "20231111"

import re

from llmkira.sdk import resign_plugin_executor
from llmkira.sdk.func_calling import verify_openapi_version
from llmkira.sdk.schema import File, Function

verify_openapi_version(__package__name__, __openapi_version__)
from io import BytesIO
from math import floor

from PIL import Image
from loguru import logger
from pydantic import BaseModel

from llmkira.schema import RawMessage
from llmkira.sdk.func_calling import BaseTool
from llmkira.sdk.func_calling.schema import FuncPair, PluginMetadata
from llmkira.task import Task, TaskHeader
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from llmkira.sdk.schema import TaskBatch
sticker = Function(name=__plugin_name__, description="Help user convert pictures to stickers")
sticker.add_property(
    property_name="yes_no",
    property_description="Is this run allowed (yes/no) If there a picture, please say yes",
    property_type="string",
    required=True
)
sticker.add_property(
    property_name="comment",
    property_description="thanks for this run",
    property_type="string",
    required=True
)


class Sticker(BaseModel):
    yes_no: str
    comment: str = "done"
    model_config = ConfigDict(extra="allow")

    @field_validator("yes_no")
    def delay_validator(cls, v):
        if v != "yes":
            v = "no"
        return v


@resign_plugin_executor(function=sticker)
async def resize_image(photo):
    logger.debug(f"Plugin:resize_image")
    image = Image.open(photo)
    if (image.width and image.height) < 512:
        size1 = image.width
        size2 = image.height
        if image.width > image.height:
            scale = 512 / size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512 / size2
            size1new = size1 * scale
            size2new = 512
        size1new = floor(size1new)
        size2new = floor(size2new)
        size_new = (size1new, size2new)
        image = image.resize(size_new)
    else:
        maxsize = (512, 512)
        image.thumbnail(maxsize)

    return image


class StickerTool(BaseTool):
    """
    搜索工具
    """
    function: Function = sticker
    keywords: list = ["转换", "贴纸", ".jpg", "图像", '图片']
    file_match_required: Optional[re.Pattern] = re.compile(r"(.+).jpg|(.+).png|(.+).jpeg|(.+).gif|(.+).webp|(.+).svg")

    def pre_check(self):
        return True

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

    async def failed(self,
                     task: "TaskHeader", receiver: "TaskHeader.Location",
                     exception,
                     env: dict,
                     arg: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                     **kwargs
                     ):
        _meta = task.task_meta.reply_notify(
            plugin_name=__plugin_name__,
            callback=[TaskHeader.Meta.Callback.create(
                tool_call_id=pending_task.get_batch_id(),
                function_response=f"Run Failed {exception}",
                name=__plugin_name__
            )],
            write_back=False,
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
        return None

    async def run(self,
                  task: "TaskHeader", receiver: "TaskHeader.Location",
                  arg: dict, env: dict, pending_task: "TaskBatch", refer_llm_result: dict = None,
                  ):
        """
        处理message，返回message
        """
        _file = []
        for item in task.message:
            assert isinstance(item, RawMessage), "item must be RawMessage"
            if item.file:
                for i in item.file:
                    _file.append(i)
        _set = Sticker.model_validate(arg)
        _file_obj = [await i.raw_file() for i in sorted(set(_file), key=_file.index)]
        # 去掉None
        _file_obj = [item for item in _file_obj if item]
        _result = []
        if not _file_obj:
            return
        for item in _file_obj:
            image = await resize_image(BytesIO(item.file_data))
            file = BytesIO()
            file.name = "sticker.webp"
            image.save(file, "WEBP")
            file.seek(0)
            file_obj = await File.upload_file(file_name="sticker.webp",
                                              file_data=file.getvalue(),
                                              created_by=__plugin_name__
                                              )
            _result.append(file_obj)
        # META
        _meta = task.task_meta.reply_message(
            plugin_name=__plugin_name__,
            callback=[
                TaskHeader.Meta.Callback.create(
                    name=__plugin_name__,
                    function_response="Run Success",
                    tool_call_id=pending_task.get_batch_id()
                )
            ],
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
                        text="Here is your sticker!"
                    )
                ]
            )
        )

        logger.debug("convert_to_sticker say: {}".format(_set.yes_no))


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Convert pictures to stickers",
    usage=str(StickerTool().keywords),
    openapi_version=__openapi_version__,
    function={
        FuncPair(function=sticker, tool=StickerTool)
    },
)
