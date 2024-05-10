from typing import Optional

from loguru import logger

from llmkira.kv_manager._base import KvManager
from llmkira.openai.cell import ToolCall

TOOLCALL_EXPIRE_TIME = 60 * 60 * 24


class ToolCallCache(KvManager):
    def prefix(self, key: str) -> str:
        return f"tool_call:{key}"

    async def save_toolcall(
        self,
        tool_call_id: str,
        tool_call: ToolCall,
    ) -> str:
        """
        Pair a tool call with a unique ID.
        """
        logger.debug(f"Save tool call {tool_call_id}")
        await self.save_data(
            tool_call_id, tool_call.model_dump_json(), timeout=TOOLCALL_EXPIRE_TIME
        )
        return tool_call_id

    async def get_toolcall(self, tool_call_id: str) -> Optional[ToolCall]:
        """
        Get a tool call by its ID.
        """
        logger.debug(f"Get tool call {tool_call_id}")
        result = await self.read_data(tool_call_id)
        if isinstance(result, bytes):
            result = result.decode("utf-8")
        if result is None:
            return None
        if isinstance(result, dict):
            return ToolCall.model_validate(result)
        return ToolCall.model_validate_json(result)


GLOBAL_TOOLCALL_CACHE_HANDLER = ToolCallCache()
