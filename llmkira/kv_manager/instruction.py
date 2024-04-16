from llmkira.kv_manager._base import KvManager

DEFAULT_INSTRUCTION = "ACT STEP BY STEP, SPEAK IN MORE CUTE STYLE"


class InstructionManager(KvManager):
    def __init__(self, user_id: str):
        self.user_id = str(user_id)

    def prefix(self, key: str) -> str:
        return f"instruction:{key}"

    async def read_instruction(self) -> str:
        result = await self.read_data(self.user_id)
        if not result:
            return DEFAULT_INSTRUCTION
        return result

    async def set_instruction(self, instruction: str) -> str:
        if not isinstance(instruction, str):
            raise ValueError("Instruction should be str")
        await self.save_data(self.user_id, instruction)
        return instruction
