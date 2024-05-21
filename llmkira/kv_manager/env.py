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
    env_table = {}
    for match in matches:
        env_key = f"{match[0]}"
        env_value = f"{match[1]}"
        env_value = env_value.strip().strip('"')
        env_key = env_key.upper()
        if env_value.upper() == "NONE":
            env_value = None
        env_table[env_key] = env_value
    return env_table


class EnvManager(KvManager):
    def __init__(self, user_id: str):
        self.user_id = str(user_id)

    def prefix(self, key: str) -> str:
        return f"env:{key}"

    async def get_env(self, env_name, default) -> Optional[str]:
        result = await self.read_env()
        if not result:
            return default
        return result.get(env_name, default)

    async def read_env(self) -> Optional[dict]:
        result = await self.read_data(self.user_id)
        if isinstance(result, bytes):
            result = result.decode("utf-8")
        if not result:
            return None
        try:
            if isinstance(result, dict):
                return result
            return json.loads(result)
        except Exception as e:
            logger.error(
                f"operation failed: env string cant be parsed by json.loads {e}"
            )
            return None

    async def set_env(
        self, env_value: Union[dict, str], update=False, return_all=False
    ) -> Dict[str, str]:
        current_env = {}
        if update:
            current_env = await self.read_env()
            if not current_env:
                current_env = {}
        if isinstance(env_value, str):
            env_map = parse_env_string(env_value)
        elif isinstance(env_value, dict):
            env_map = env_value
        else:
            raise ValueError("Env String Should be dict or str")
        # 更新
        current_env = {**current_env, **env_map}
        # 去除 None
        current_env = {k: v for k, v in current_env.items() if v is not None}
        await self.save_data(self.user_id, json.dumps(current_env))
        if return_all:
            return current_env
        return env_map
