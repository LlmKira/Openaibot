# -*- coding: utf-8 -*-
# @Time    : 2023/3/29 下午10:24
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import pathlib

from .Censor import Censor, DFA

from pydantic import BaseSettings, SecretStr


class DatabaseSettings(BaseSettings):
    host: str
    port: int


class Settings(BaseSettings):
    app_name: str = "My App"
    admin_email: str
    items_per_page: int = 10
    database: DatabaseSettings = None

    class Config:
        env_prefix = "MY_APP_"

    @classmethod
    def custom_config_source(cls, secrets_path: str):
        with open(secrets_path) as f:
            secrets = json.load(f)
        return {"database": DatabaseSettings(**secrets["database"])}

    @validator("admin_email")
    def validate_admin_email(cls, v):
        if not v.endswith("@example.com"):
            raise ValueError("admin_email must be a valid example.com email address")
        return v


settings = Settings(_env_file=".env", secrets_path="/path/to/secrets.json")  # 自定义配置源

CENSOR_URL = {
    "Danger.form": [
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2Z3d2RuL3NlbnNpdGl2ZS1zdG9wLXdvcmRzL21hc3Rlci8lRTYlOTQlQkYlRTYlQjIlQkIlRTclQjElQkIudHh0",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL1RlbGVjaGFCb3QvQW50aVNwYW0vbWFpbi9EYW5nZXIudHh0",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FkbGVyZWQvRGFuZ2Vyb3VzU3BhbVdvcmRzL21hc3Rlci9EYW5nZXJvdXNTcGFtV29yZHMvR2VuZXJhbF9TcGFtV29yZHNfVjEuMC4xX0NOLm1pbi50eHQ=",
        "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0phaW1pbjEzMDQvc2Vuc2l0aXZlLXdvcmQtZGV0ZWN0b3IvbWFpbi9zYW1wbGVfZmlsZXMvc2FtcGxlX2Jhbm5lZF93b3Jkcy50eHQ=",
    ]
}

# 数据类
if not pathlib.Path("./Data/Danger.form").exists():
    Censor.initialize_word_lists(urls=CENSOR_URL, home_dir="./Data/", proxy=proxy)

# Initialize content filter
ContentDfa = DFA(path="./Data/Danger.form")
