# 关于 Function Call

## 1. 样板代码

```python
from typing import Literal


def get_current_weather(location: str, format: Literal["fahrenheit", "celsius"]):
    """
    Get the current weather
    :param location: The city and state, e.g. San Francisco, CA
    :param format: The temperature unit to use. Infer this from the users location.
    """
```

### Pydantic 数据模型

pydantic 的数据模型，不完全兼容 openapi

```json5

{
  'title': 'Search',
  'description': '测试搜索类型',
  'type': 'object',
  'properties': {
    'keywords': {
      'title': 'Keywords',
      'description': '关键词',
      'type': 'string'
    },
    'text': {
      'title': 'Text',
      'description': '文本',
      'type': 'string'
    }
  }
}

```

这点 langchain 相关开发有提到
https://github.com/minimaxir/simpleaichat/issues/40
https://github.com/minimaxir/simpleaichat/blob/1dead657731e0d2a4df608a7aa94b86322412851/examples/notebooks/schema_ttrpg.ipynb
https://api.python.langchain.com/en/latest/_modules/langchain/tools/convert_to_openai.html#format_tool_to_openai_function

## 标准化格式演示

```json5
[
  {
    'name': 'get_current_weather',
    'description': 'Get the current weather',
    'parameters': {
      'type': 'object',
      'properties': {
        'location': {
          'description': 'The city and state, e.g. San Francisco, CA',
          'type': 'string'
        },
        'format': {
          'description': 'The temperature unit to use. Infer this from the users location.',
          'type': 'string',
          'enum': [
            'fahrenheit',
            'celsius'
          ]
        }
      }
    },
    'required': [
      'location',
      'format'
    ]
  }
]

```

## 样板消息

```python
example_messages = [
    {
        "role": "system",
        "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "New synergies will help drive top-line growth.",
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": "Things working well together will increase revenue.",
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": "Let's talk later when we're less busy about how to do better.",
    },
    {
        "role": "user",
        "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
    },
]
```


## 备注

`Open AI does not support an array type`
