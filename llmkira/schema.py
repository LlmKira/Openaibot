# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 下午9:31
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
import time
from typing import TYPE_CHECKING, Literal, Type, Optional
from typing import Union, List

import nest_asyncio
from pydantic import field_validator, ConfigDict, Field, BaseModel

from .sdk.endpoint.tokenizer import get_tokenizer
from .sdk.schema import File, generate_uid, UserMessage, Message

if TYPE_CHECKING:
    from .task import TaskHeader

nest_asyncio.apply()


class RawMessage(BaseModel):
    user_id: Union[int, str] = Field(None, description="user id")
    chat_id: Union[int, str] = Field(None, description="guild id(channel in dm)/Telegram chat id")
    thread_id: Optional[Union[int, str]] = Field(None, description="channel id/Telegram thread")

    text: str = Field("", description="文本")
    file: List[File] = Field([], description="文件")

    created_at: str = Field(default=str(int(time.time())), description="创建时间")
    only_send_file: bool = Field(default=False, description="Send file only")

    sign_loop_end: bool = Field(default=False, description="要求其他链条不处理此消息，用于拦截器开发")
    sign_fold_docs: bool = Field(default=False, description="是否获取元数据")
    extra_kwargs: dict = Field(default={}, description="extra kwargs for loop")
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @field_validator("text")
    def check_text(cls, v):
        if v == "":
            v = ""
        if len(v) > 4096:
            v = v[:4090]
        return v

    def format_user_message(
            self,
            role: Literal["system", "assistant", "user", "function", "tool"] = "user",
            name: str = None
    ) -> UserMessage:
        """
        OpenAI 格式化
        """
        return UserMessage(
            role=role,
            name=name,
            content=self.text,
        ).update_meta(meta=Message.Meta(
            retrieval=self.sign_fold_docs,
            files=self.file,
            index_id=self.thread_id or generate_uid(),
        )
        )

    @classmethod
    def format_openai_message(
            cls,
            message: Type[Message],
            locate: "TaskHeader.Location"
    ) -> "RawMessage":
        """
        用于 OpenAI 消息转换回复给用户
        """
        # IMPORT FROM llmkira.task
        return cls(
            user_id=locate.user_id,
            text=message.content,
            chat_id=locate.chat_id,
            created_at=str(int(time.time()))
        )


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


class Scraper(BaseModel):
    """
    刮削器
    始终按照顺序排列，削除得分低的条目
    Scraper is a class that sorts a list of messages_box by their score.
    """

    class Sorter(BaseModel):
        message: Union[Type[Message], Message]
        score: float
        order: int

        def get_message(self) -> Union[Type[Message], Message]:
            return self.message

    messages_box: List[Sorter] = []
    # 最大消息数
    max_messages: int = 12
    # 计数器
    tick: int = 0

    # 方法：添加消息
    def add_message(self, message: Union[Type[Message], Message], score: float):
        if not hasattr(message, "content"):
            """message has no content"""
            return None
        self.messages_box.append(self.Sorter(message=message, score=score, order=self.tick))
        self.tick += 1
        # 按照顺序排序
        self.messages_box.sort(key=lambda x: x.order)
        while len(self.messages_box) > self.max_messages:
            self.messages_box.pop(0)

    # 方法：获取消息
    def get_messages(
            self
    ) -> List[Union[Type[Message], Message]]:
        _message: List[Union[Type[Message], Message]] = []
        for sorter in self.messages_box:
            assert isinstance(sorter.message, Message), f"message type error {type(sorter.message)}"
            _message.append(sorter.message)
        return _message

    def build_messages(self):
        # 只取三个，末位匹配
        _message = self.get_messages()
        if len(_message) < 3:
            return _message
        _build = []
        _must = _message[-3:]
        _check_list = _message[:-3]
        _match_sentence = _message[-1:][0].content
        for item_obj in _check_list:
            _build.append(item_obj)
            # NOTICE 此处被内存优化，不再使用
            """
            if Sim.cos ion_similarity(pre=_match_sentence, aft=item_obj.content) < 0.9:
                _build.append(item_obj)
            else:
                pass
                # logger.warning(f"ignore sim item {item_obj}")
            """
        _build.extend(_must)
        return _build

    # 方法：获取消息数
    def get_num_messages(self) -> int:
        return len(self.messages_box)

    def fold_message(self):
        """
        以折叠形态出击
        """
        for sorter in self.messages_box:
            if sorter.get_message().get_meta().retrieval:
                sorter.message = sorter.message.fold
        return self

    # 方法：清除消息到负载
    def reduce_messages(self,
                        *,
                        limit: int = 2048,
                        model_name: str
                        ):
        """
        对齐 0.7 倍极限的消息记录
        :param limit: 最大字数
        :param model_name: 模型名称
        :return: None
        """
        # 预留位
        if limit > 1000:
            limit = limit * 0.8
        else:
            limit = limit * 0.7
        # 执行删除操作
        if get_tokenizer(model_name=model_name).num_tokens_from_messages(
                messages=self.get_messages(),
                model=model_name
        ) > limit:
            # 从最旧开始删除
            self.messages_box.sort(key=lambda x: x.order)
            while get_tokenizer(model_name=model_name).num_tokens_from_messages(
                    messages=self.get_messages(),
                    model=model_name
            ) > limit:
                if len(self.messages_box) > 1:
                    self.messages_box.pop(0)
                else:
                    self.messages_box[0].message.content = self.messages_box[0].message.content[:limit]
        # 按照顺序排序
        self.messages_box.sort(key=lambda x: x.order)
