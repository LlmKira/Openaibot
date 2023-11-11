# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 上午11:06
# @Author  : sudoskys
# @File    : components.py
# @Software: PyCharm
import base64
import hashlib
import pickle
import time
from abc import abstractmethod, ABC
from io import BytesIO
from typing import Literal, Optional, List, Type, Union
from typing import TYPE_CHECKING

import shortuuid
from loguru import logger
from pydantic import BaseModel, root_validator, Field, PrivateAttr

from .error import ValidationError, CheckError
from .utils import sync

if TYPE_CHECKING:
    pass


# ATTENTION:禁止调用上层任何schema包，否则会导致循环引用

def generate_uid():
    return shortuuid.uuid()[0:8].upper()


class File(BaseModel):
    """
    请求体
    可提供标准化的文件定义。
    但是不能直接提供接口标准化，因为文件上传需要特殊处理
    """

    class Data(BaseModel):
        file_name: str
        file_data: bytes = Field(None, description="文件数据")

        @property
        def pair(self):
            return self.file_name, self.file_data

    file_id: Optional[str] = Field(None, description="文件ID")
    file_name: str = Field(None, description="文件名")
    file_url: str = Field(None, description="文件URL")
    caption: str = Field(default='', description="文件注释")
    bytes: int = Field(default=None, description="文件大小")
    created_by: str = Field(default=None, description="上传者")
    created_at: int = Field(default=int(time.time()))

    def __eq__(self, other):
        if isinstance(other, File):
            return (self.file_id == other.file_id) and (self.file_name == other.file_name)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.file_id) + hash(self.file_name)

    def is_user_upload(self, uid: str):
        """
        判断是否是某个用户上传的
        """
        return self.created_by == uid

    @property
    def file_prompt(self):
        """
        FOR LLM
        """
        _comment = '('
        for key, value in self.dict().items():
            if value:
                _comment += f"{key}={value},"
        return f"[Attachment{_comment[:-1]})]"

    @staticmethod
    async def download_file_by_id(
            file_id: str,
    ) -> Optional[Data]:
        from .cache.redis import cache
        file = await cache.read_data(file_id)
        if not file:
            return None
        file_obj: File.Data = pickle.loads(file)
        return file_obj

    async def raw_file(
            self,
    ) -> Optional[Data]:
        from .cache.redis import cache
        if not self.file_id:
            return None
        file = await cache.read_data(self.file_id)
        if not file:
            return None
        file_obj: File.Data = pickle.loads(file)
        return file_obj

    @classmethod
    async def upload_file(cls,
                          file_name,
                          file_data,
                          created_by: str,
                          caption: str = None,
                          ):
        from .cache.redis import cache
        _byte_length = len(file_data)
        _key = str(generate_md5_short_id(file_data))
        await cache.set_data(
            key=_key,
            value=pickle.dumps(File.Data(file_name=file_name, file_data=file_data)),
            timeout=60 * 60 * 24 * 7
        )
        return cls(file_id=_key,
                   file_name=file_name,
                   bytes=_byte_length,
                   created_by=created_by,
                   caption=caption,
                   )

    @classmethod
    async def upload_file_by_url(cls,
                                 file_name,
                                 file_url,
                                 created_by: str,
                                 caption: str = None,
                                 ):
        return cls(file_id=None,
                   file_url=file_url,
                   file_name=file_name,
                   created_by=created_by,
                   caption=caption,
                   )


class BaseFunction(BaseModel):
    """
    请求体
    只供 Choice 使用
    """

    class FunctionExtra(BaseModel):
        system_prompt: str = Field(None, description="系统提示")

        @classmethod
        def default(cls):
            return cls(system_prompt=None)

    _config: FunctionExtra = FunctionExtra.default()
    name: str = Field(None, description="函数名称", regex=r"^[a-zA-Z0-9_]+$")

    def update_config(self, config: FunctionExtra) -> "BaseFunction":
        self._config = config
        return self

    def update_system_prompt(self, prompt: str) -> "BaseFunction":
        self._config.system_prompt = prompt
        return self

    @property
    def config(self) -> FunctionExtra:
        return self._config

    def request_final(self,
                      *,
                      schema_model: str):
        return self.copy(
            include={"name"}
        )


class Function(BaseFunction):
    """
    请求体
    供外部模组定义并注册函数
    """

    class Parameters(BaseModel):
        type: str = "object"
        properties: dict = {}
        required: List[str] = Field(default=[], description="必填参数")

    name: str = Field(None, description="函数名称", regex=r"^[a-zA-Z0-9_]+$")
    description: Optional[str] = None
    parameters: Parameters = Parameters(type="object")

    def request_final(self,
                      *,
                      schema_model: str):
        """
        标准化
        :param schema_model: 适配的模型
        """
        if schema_model.startswith("gpt-"):
            return self.copy(
                include={"name", "description", "parameters"}
            )
        elif schema_model.startswith("chatglm"):
            return self.copy(
                include={"name", "description", "parameters"}
            )
        else:
            raise CheckError(f"unknown model {schema_model}, cant classify model type")

    def add_property(self,
                     property_name: str,
                     property_type: Literal["string", "integer", "number", "boolean", "object"],
                     property_description: str,
                     enum: Optional[tuple] = None,
                     required: bool = False
                     ):
        """
        加注属性
        """
        self.parameters.properties[property_name] = {}
        self.parameters.properties[property_name]['type'] = property_type
        self.parameters.properties[property_name]['description'] = property_description
        if enum:
            self.parameters.properties[property_name]['enum'] = tuple(enum)
        if required:
            self.parameters.required.append(property_name)

    def parse_schema_to_properties(self, schema: Type[BaseModel]):
        """
        解析 pydantic 的 schema
        """
        self.parameters.properties = schema.schema()["properties"]
        self.parameters.required = schema.schema()["required"]


class FunctionCallCompletion(BaseModel):
    name: str
    arguments: str


class Tool(BaseModel):
    """
    请求体
    """
    type: str = Field(default="function")
    function: Function

    def request_final(
            self,
            *,
            schema_model
    ):
        if schema_model.startswith("gpt-"):
            return self.copy(
                include={"type", "function"},
            )
        elif schema_model.startswith("chatglm"):
            return self.copy(
                include={"type", "function"},
            )
        else:
            return self.copy(
                include={"type", "function"},
            )
            # raise CheckError(f"unknown model {schema_model}, cant classify model type")


class ToolChoice(BaseModel):
    """
    请求体
    """
    type: str = Field(default=None)
    function: BaseFunction = Field(default=None)


class ToolCallCompletion(ToolChoice):
    """
    响应
    """
    id: str = Field(default=None)
    type: str = Field(default=None)
    function: FunctionCallCompletion = Field(default=None)


class TaskBatch(BaseModel):
    id: str = Field(default=None)
    type: str = Field(default=None)
    function: FunctionCallCompletion = Field(default=None)

    @classmethod
    def from_tool_call(cls, tool_call: ToolCallCompletion):
        if not tool_call:
            return None
        return cls(
            id=tool_call.id,
            type=tool_call.type,
            function=tool_call.function
        )

    @classmethod
    def from_function_call(cls, function_call: FunctionCallCompletion):
        if not function_call:
            return None
        return cls(
            id=None,
            type="function",
            function=function_call
        )

    def get_batch_name(self):
        return self.function.name

    def get_batch_args(self):
        return self.function.arguments

    def get_batch_id(self):
        return self.id


class ContentParts(BaseModel):
    """
    请求体
    """

    class Image(BaseModel):
        url: str
        detail: Optional[str]

    type: str
    image_url: Optional[str]
    text: Optional[str]


class Message(BaseModel, ABC):
    """
    请求体
    响应体
    """

    class Meta(BaseModel):
        # message_class: Literal[None, "system", "user", "assistant", "tool", "function"] = Field(default="user")
        index_id: str = Field(default_factory=generate_uid, description="消息ID")
        """消息ID"""

        datatime: str = Field(default=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), description="消息时间")
        timestamp: int = Field(default=int(time.time()), description="消息时间戳")
        """消息时间"""

        retrieval: bool = Field(default=False, description="是否可检索")
        """是否折叠(对抗过长消息，为小上下文模型设计)，同时证明我们可以在消息嵌入重整策略"""

        extra: dict = Field(default_factory=dict, description="额外信息")
        """额外信息"""

        files: List[File] = Field(default_factory=list, description="文件信息")
        """文件信息"""

        @classmethod
        def default(cls, message_class):
            return cls(message_class=message_class)

    _meta: Meta = PrivateAttr(default=None)
    """元数据"""
    role: str
    content: Union[str, List[ContentParts], list[dict]]

    def get_meta(self) -> Meta:
        return self._meta

    def update_meta(self, meta: Meta) -> "Message":
        self._meta = meta
        return self

    @property
    def fold(self) -> "Message":
        return self

    def get_functions(self) -> List[TaskBatch]:
        raise NotImplementedError

    @abstractmethod
    def request_final(self,
                      schema_model: str,

                      ) -> "Message":
        """
        Openai 请求标准格式最终转换根据 message_class 元信息锁定字段
        :param schema_model: 适配的模型
        """
        raise NotImplementedError


class SystemMessage(Message):
    role: str = Field(default="system")
    content: str
    name: Optional[str] = Field(default=None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")

    def request_final(self,
                      *,
                      schema_model: str,
                      ) -> "Message":
        return self


class UserMessage(Message):
    role: str = Field(default="user")
    content: Union[str, List[ContentParts], list[dict]]
    name: Optional[str] = Field(default=None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")

    @property
    def fold(self) -> "Message":
        """
        折叠过长特殊类型消息。消息类型为程序自有属性
        插件定义 fold_id 引诱查询
        :return: Message
        """
        metadata_str = (f"""[FoldText](fold_id={self._meta.index_id}"""
                        f"""\ntimestamp={self._meta.datatime}"""
                        f"""\ndescription={self.content[:20] + "..."})"""
                        )
        return self.copy(
            update={
                "content": metadata_str
            },
            include={"role", "content", "name"}
        )

    def request_final(self,
                      *,
                      schema_model: str,
                      ) -> "Message":
        """
        Openai 请求标准格式最终转换根据 message_class 元信息锁定字段
        :param schema_model: 适配的模型
        """
        if "vision" in schema_model:
            if isinstance(self.content, str):
                _new_content: List[ContentParts] = [ContentParts(
                    type="text",
                    text=self.content
                )]
                if self._meta.files:
                    for file in self._meta.files:
                        if file.file_url:
                            _new_content.append(
                                ContentParts(
                                    type="image_url",
                                    image_url=file.file_url
                                )
                            )
                        elif file.file_id:
                            if file.file_name.endswith(("jpg", "png", "jpeg", "gif", "webp", "svg")):
                                base64_image = base64.b64encode(
                                    sync(file.raw_file())
                                ).decode('utf-8')
                                _new_content.append(
                                    ContentParts(
                                        type="image_url",
                                        image_url=f"data:image/png;base64,{base64_image}"
                                    )
                                )
                        else:
                            pass
                self.content = _new_content
        return self


class AssistantMessage(Message):
    role: str = Field(default="assistant")
    content: Union[None, str] = Field(default='', description="assistant content")
    name: Optional[str] = Field(default=None, description="speaker_name", regex=r"^[a-zA-Z0-9_]+$")
    tool_calls: Optional[List[ToolCallCompletion]] = Field(default=None, description="tool calls")
    """a array of tools, for result"""
    function_call: Optional[FunctionCallCompletion] = Field(default=None, description="Deprecated")
    """Deprecated by openai ,for result"""

    @root_validator()
    def deprecate_validator(cls, values):
        if values.get("tool_calls") and values.get("function_call"):
            raise ValidationError("sdk param validator:tool_calls and function_call cannot both be provided")
        if values.get("function_call"):
            logger.warning("sdk param validator:function_call is deprecated")
        if values.get("content") is None:
            values["content"] = ""
        return values

    def get_executor_batch(self) -> List[TaskBatch]:
        """
        获取插件获取对应的无序函数列表，合并新旧标准
        """
        _calls = []
        if self.function_call:
            _calls.append(TaskBatch.from_function_call(self.function_call))
        _calls.extend([TaskBatch.from_tool_call(tools) for tools in self.tool_calls])
        # 去None
        _calls = [_x for _x in _calls if _x]
        return _calls

    @property
    def sign_function(self) -> bool:
        """
        判断是否有函数需要执行
        """
        if self.function_call:
            return True
        if self.tool_calls:
            for tol in self.tool_calls:
                if tol.function:
                    return True
        return False

    def request_final(self,
                      *,
                      schema_model: str,
                      ) -> "Message":
        return self


class ToolMessage(Message):
    role: str = Field(default="tool")
    content: str
    tool_call_id: str

    def request_final(self,
                      *,
                      schema_model: str,
                      ) -> "Message":
        return self


class FunctionMessage(Message):
    role: str = Field(default="function")
    content: str
    name: str

    @root_validator()
    def function_validator(cls, values):
        logger.warning("Function Message is deprecated by openai")
        if values.get("role") == "function" and not values.get("name"):
            raise ValidationError("sdk param validator:name must be specified when role is function")
        return values

    def request_final(self,
                      *,
                      schema_model: str,
                      ) -> "Message":
        """
        Openai 请求标准格式最终转换根据 message_class 元信息锁定字段
        :param schema_model: 适配的模型
        """
        return self


def create_short_task(task_desc, refer, role: str = None):
    """
    创建单任务模板
    """
    if not role:
        role = (
            "[RULE]"
            "Please complete the order according to the task description refer to given information, "
            "if can't complete, please reply 'give up'"
        )
    return [
        SystemMessage(
            role="system",
            content=role,
        ),
        UserMessage(
            role="user",
            content=f"{refer} <hint>{task_desc}<hint>",
            name="task"
        )
    ]


def parse_message_dict(item: dict):
    """
    将 dict 实例化，用错误hook覆盖
    """
    role = item.get("role", None)
    if not role:
        return None
    try:
        if role == "assistant":
            _message = AssistantMessage.parse_obj(item)
        elif role == "user":
            _message = UserMessage.parse_obj(item)
        elif role == "system":
            _message = SystemMessage.parse_obj(item)
        elif role == "tool":
            _message = ToolMessage.parse_obj(item)
        elif role == "function":
            _message = FunctionMessage.parse_obj(item)
        else:
            raise CheckError(f"unknown message type {role}")
    except Exception as e:
        logger.exception(f"[ParseError]\nparse_message_dict:Unknown message type in redis data:\n{e}")
        return None
    else:
        return _message


def standardise_for_request(
        *,
        message: "Message",
        schema_model: str
) -> "Message":
    """
    标准化转换，供请求使用
    """
    if isinstance(message, dict):
        message = Message.parse_obj(message)
    if hasattr(message, "message"):
        return message.request_final(schema_model=schema_model)
    else:
        return message


def generate_md5_short_id(data):
    # 检查输入数据是否是一个文件
    is_file = False
    if isinstance(data, str):
        is_file = True
    if isinstance(data, BytesIO):
        data = data.getvalue()
    # 计算 MD5 哈希值
    md5_hash = hashlib.md5()
    if is_file:
        with open(data, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
    else:
        md5_hash.update(data)
    # 获取哈希值的 16 进制表示
    hex_digest = md5_hash.hexdigest()
    # 生成唯一的短ID
    short_id = hex_digest[:8]
    return short_id
