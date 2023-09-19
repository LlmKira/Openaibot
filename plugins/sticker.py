# -*- coding: utf-8 -*-
# @Time    : 2023/8/19 上午12:09
# @Author  : sudoskys
# @File    : sticker.py
# @Software: PyCharm
from io import BytesIO
from math import floor

from PIL import Image
from loguru import logger
from pydantic import validator, BaseModel

from schema import TaskHeader, RawMessage
from sdk.endpoint.openai import Function
from sdk.func_call import BaseTool, listener
from task import Task

__plugin_name__ = "convert_to_sticker"
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

    class Config:
        extra = "allow"

    @validator("yes_no")
    def delay_validator(cls, v):
        if v != "yes":
            v = "no"
        return v


async def resize_image(photo):
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


@listener(function=sticker)
class StickerTool(BaseTool):
    """
    搜索工具
    """
    function: Function = sticker
    keywords: list = ["转换", "贴纸", ".jpg", "图像", '图片']

    def pre_check(self):
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
                            text="🍖 操作失败，原因：{}".format(reason)
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(e)

    async def run(self, task: TaskHeader, receiver: TaskHeader.Location, arg, **kwargs):
        """
        处理message，返回message
        """
        try:
            _file = []
            for item in task.message:
                if item.file:
                    for i in item.file:
                        _file.append(i)
            _set = Sticker.parse_obj(arg)
            _file_obj = [await RawMessage.download_file(file_id=i.file_id) for i in sorted(set(_file), key=_file.index)]
            # 去掉None
            _file_obj = [BytesIO(item) for item in _file_obj if item]
            _result = []
            if not _file_obj:
                return
            for item in _file_obj:
                image = await resize_image(item)
                file = BytesIO()
                file.name = "sticker.webp"
                image.save(file, "WEBP")
                file.seek(0)
                file_obj = await RawMessage.upload_file(name="sticker.webp", data=file.getvalue())
                _result.append(file_obj)

            await Task(queue=receiver.platform).send_task(
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
                            file=_result,
                            text=_set.comment
                        )
                    ]
                )
            )

            logger.debug("convert_to_sticker say: {}".format(_set.yes_no))
        except Exception as e:
            logger.exception(e)
            await self.failed(platform=receiver.platform, task=task, receiver=receiver, reason=str(e))
