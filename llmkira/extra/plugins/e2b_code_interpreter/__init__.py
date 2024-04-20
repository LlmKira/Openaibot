# -*- coding: utf-8 -*-
import base64
import io
from typing import Union, Type, List, Tuple

from e2b_code_interpreter import CodeInterpreter, Result as E2BResult
from loguru import logger
from pydantic import ConfigDict

__package__name__ = "llmkira.extra.plugins.e2b_code_interpreter"
__plugin_name__ = "exec_code"
__openapi_version__ = "20240416"

from llmkira.kv_manager.file import File
from llmkira.sdk.tools import verify_openapi_version  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

verify_openapi_version(__package__name__, __openapi_version__)  # noqa: E402
from llmkira.openai.cell import Tool, ToolCall, class_tool  # noqa: E402
from llmkira.sdk.tools import PluginMetadata  # noqa: E402
from llmkira.sdk.tools.schema import FuncPair, BaseTool  # noqa: E402
from llmkira.task import Task, TaskHeader  # noqa: E402
from llmkira.task.schema import Location, ToolResponse, EventMessage  # noqa: E402


class exec_python(BaseModel):
    """
    Executes the passed Python code in Jupyter Notebook and returns the stdout.
    """

    cells: List[str] = Field(
        description="The Python code cells to execute. such as !pip install matplotlib"
    )
    model_config = ConfigDict(extra="allow")


def parse_e2b_jupyter_output(results: List[E2BResult]):
    file_list = []
    format_suffix_map = {
        "html": "html", "markdown": "md", "svg": "svg", "png": "png",
        "jpeg": "jpeg", "pdf": "pdf", "latex": "latex", "json": "json",
        "javascript": "js", "txt": "txt"
    }
    for exc in results:
        for fort in exc.formats():
            logger.debug(f"e2b return format: {fort}")
            content = getattr(exc, fort, None)
            if content:
                file_ = base64.b64decode(content)
                file_io = io.BytesIO(file_)
                file_suffix = format_suffix_map.get(fort, "txt")
                file_name = f"e2b_{fort}.{file_suffix}"
                logger.debug(f"e2b return format: {file_name}")
                file_list.append((file_name, file_io))
    return file_list


# @resign_plugin_executor(tool=exec_code)
async def exec_code_by_e2b(
    cells: List[str], api_key: str = None
) -> Tuple[str, List[Tuple[str, io.BytesIO]]]:
    if not api_key:
        raise ValueError("api key from https://e2b.dev/ is required")
    logger.debug(f"E2b:cells: {cells}")
    try:
        with CodeInterpreter(api_key=api_key) as sandbox:
            # 执行除了最后一个cell之外的所有cell
            for cell in cells[:-1]:
                sandbox.notebook.exec_cell(cell)
            # 执行最后一个cell
            execution = sandbox.notebook.exec_cell(cells[-1])
    except Exception as e:
        logger.error(f"E2b:Error: {e}")
        return f"Error: {e}", []
    file_list = parse_e2b_jupyter_output(execution.results)
    logger.debug(f"E2b:result: {execution.text}\n error: {execution.error}")
    return f"Result: {execution.text}\n Error: {execution.error}", file_list


class CodeInterpreterTool(BaseTool):
    """
    搜索工具
    """

    silent: bool = False
    function: Union[Tool, Type[BaseModel]] = exec_python
    keywords: list = [
        "exec ",
        "code ",
        "python ",
        "Python",
        "函数",
        "绘制",
        "Jupyter",
        "JavaScript",
        "Help me",
        "Draw",
        "javascript ",
        "nodejs ",
        "代码",
        "沙箱",
        "执行",
        "计算",
    ]
    env_required: List[str] = ["E2B_KEY"]
    env_prefix: str = "CODE_"

    def require_auth(self, env_map: dict) -> bool:
        if env_map.get("CODE_E2B_KEY", None) is None:
            return True
        return False

    @classmethod
    def env_help_docs(cls, empty_env: List[str]) -> str:
        """
        Provide help message for environment variables
        :param empty_env: The environment variable list that not configured
        :return: The help message
        """
        message = ""
        if "CODE_E2B_KEY" in empty_env:
            message += "You need to configure https://e2b.dev/ to start use this tool"
        return message

    def func_message(self, message_text, message_raw, address, **kwargs):
        """
        如果合格则返回message，否则返回None，表示不处理
        """
        for i in self.keywords:
            if i in message_text:
                return self.function
        if message_text.endswith("?"):
            return self.function
        if message_text.endswith("？"):
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

        code_arg = exec_python.model_validate(arg)
        exec_result, files_result = await exec_code_by_e2b(
            cells=code_arg.cells,
            api_key=env.get("CODE_E2B_KEY", None),
        )
        # META
        _meta = task.task_sign.reply(
            plugin_name=__plugin_name__,
            tool_response=[
                ToolResponse(
                    name=__plugin_name__,
                    function_response=str(exec_result),
                    tool_call_id=pending_task.id,
                    tool_call=pending_task,
                )
            ],
        )
        return_files = []
        for file in files_result:
            logger.debug(f"Upload file: {file[0]}")
            _files = await File.upload_file(
                creator=receiver.uid,
                file_name=file[0],
                file_data=file[1],
            )
            return_files.append(_files)
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
                        text="",
                        files=return_files,
                    )
                ],
            ),
        )


__plugin_meta__ = PluginMetadata(
    name=__plugin_name__,
    description="Executes the passed JavaScript code using Nodejs and returns the stdout and stderr.",
    usage="nodejs <code>",
    openapi_version=__openapi_version__,
    function={FuncPair(function=class_tool(exec_python), tool=CodeInterpreterTool)},
)
