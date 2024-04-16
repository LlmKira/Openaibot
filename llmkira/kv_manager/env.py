import json
import re
from typing import Dict, Union, Optional

from loguru import logger

from ._base import KvManager


def parse_env_string(env_string) -> Dict[str, str]:
    if not env_string.endswith(";"):
        env_string = env_string + ";"
    pattern = r"(\w+)\s*=\s*(.*?)\s*;"
    matches = re.findall(pattern, env_string, re.MULTILINE)
    _env_table = {}
    for match in matches:
        _key = match[0]
        _value = match[1]
        _value = _value.strip().strip('"')
        _key = _key.upper()
        _env_table[_key] = _value
    return _env_table


class EnvManager(KvManager):
    def __init__(self, user_id: str):
        self.user_id = str(user_id)

    def prefix(self, key: str) -> str:
        return f"env:{key}"

    async def read_env(self) -> Optional[dict]:
        result = await self.read_data(self.user_id)
        if not result:
            return None
        try:
            return json.loads(result)
        except Exception as e:
            logger.error(
                f"operation failed: env string cant be parsed by json.loads {e}"
            )
            return None

    async def set_env(
        self, env_value: Union[dict, str], update=False
    ) -> Dict[str, str]:
        current_env = {}
        if update:
            current_env = await self.read_env()
        if isinstance(env_value, str):
            env_map = parse_env_string(env_value)
        elif isinstance(env_value, dict):
            env_map = env_value
        else:
            raise ValueError("Env String Should be dict or str")
        current_env.update(env_map)
        await self.save_data(self.user_id, json.dumps(current_env))
        return env_map
