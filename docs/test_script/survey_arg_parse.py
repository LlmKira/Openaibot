import json
import re


def parse_env(env_string):
    if not env_string.endswith(";"):
        env_string = env_string + ";"
    pattern = r'(\w+)\s*=\s*(.*?)\s*;'
    matches = re.findall(pattern, env_string, re.MULTILINE)
    _env_table = {}
    for match in matches:
        _key = match[0]
        _value = match[1]
        _value = _value.strip().strip("\"")
        _key = _key.upper()
        _env_table[_key] = _value
    print(_env_table)
    return _env_table


env = """USER_NAME="admin" ;asdfasd=123;adsad=;"""

parse_env(env)
