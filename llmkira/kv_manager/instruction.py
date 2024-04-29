import time

from llmkira.kv_manager._base import KvManager

DEFAULT_INSTRUCTION = (
    "[ASSISTANT RULE]"
    "SPEAK IN MORE CUTE STYLE, No duplication answer, CALL USER MASTER, REPLY IN USER "
    "LANGUAGE, ACT STEP BY STEP"
    "[RULE END]"
)


def time_now():
    """人类可读时间"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class InstructionManager(KvManager):
    def __init__(self, user_id: str):
        self.user_id = str(user_id)

    def prefix(self, key: str) -> str:
        return f"instruction:{key}"

    async def read_instruction(self) -> str:
        """
        读取指令，如果没有指令则返回默认指令，指令长度大于5，否则返回默认指令
        """
        result = await self.read_data(self.user_id)
        if isinstance(result, str) and len(result) > 5:
            return f"Now={time_now()}\n{result}"
        return f"Now={time_now()}\n{DEFAULT_INSTRUCTION}"

    async def set_instruction(self, instruction: str) -> str:
        if not isinstance(instruction, str):
            raise ValueError("Instruction should be str")
        await self.save_data(self.user_id, instruction)
        return instruction
