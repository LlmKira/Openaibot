from typing import List

from loguru import logger

from llmkira.kv_manager.tool_call import GLOBAL_TOOLCALL_CACHE_HANDLER
from llmkira.openai.cell import Message, AssistantMessage, ToolMessage


async def validate_mock2(messages: List[Message]):
    """
    所有的具有 tool_calls 的 AssistantMessage 后面必须有对应的 ToolMessage 响应。其他消息类型按照原顺序
    """
    paired_messages = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if isinstance(msg, AssistantMessage) and msg.tool_calls:
            # 保证后续存在元素且是 ToolMessage 实例
            if i + 1 < len(messages) and isinstance(messages[i + 1], ToolMessage):
                tool_message: ToolMessage = messages[i + 1]
                assistant_message = AssistantMessage(
                    content=msg.content,
                    tool_calls=[
                        tool_call
                        for tool_call in msg.tool_calls
                        if tool_call.id == tool_message.tool_call_id
                    ],
                )
                if (
                    assistant_message.tool_calls
                ):  # 只有当有匹配的 tool_calls 时，才添加 AssistantMessage
                    paired_messages.append(assistant_message)
                    paired_messages.append(tool_message)
                    i += 1  # ToolMessage已处理，所以移动一步
                else:
                    # 尝试通过GLOBAL_TOOLCALL_CACHE_HANDLER获得 tool_call
                    tool_call_origin = await GLOBAL_TOOLCALL_CACHE_HANDLER.get_toolcall(
                        tool_message.tool_call_id
                    )
                    if tool_call_origin:
                        assistant_message = AssistantMessage(
                            content=None, tool_calls=[tool_call_origin]
                        )
                        paired_messages.append(assistant_message)
                        paired_messages.append(tool_message)
                        i += 1  # ToolMessage已处理，所以移动一步
                    else:
                        logger.error(
                            f"llm_task:ToolCall not found {tool_message.tool_call_id}, skip"
                        )
        else:
            paired_messages.append(msg)
        i += 1
    if len(paired_messages) != len(messages):
        logger.debug(f"llm_task:validate_mock cache:{paired_messages}")
    return paired_messages
