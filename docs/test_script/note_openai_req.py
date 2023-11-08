# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 下午1:43
# @Author  : sudoskys
# @File    : openai.py
# @Software: PyCharm

from llmkira.sdk.endpoint import openai
from llmkira.sdk.endpoint.tee import Driver

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
if __name__ == '__main__':
    from loguru import logger
    import asyncio

    _list = [
        {
            "role": "system",
            "content": "You are a helpful, pattern-following assistant.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "New synergies will help drive top-line growth.",
        },
        {
            "role": "user",
            "name": "Miku_Chan",
            # "content": "你知道悉尼是哪个国家的首都吗？",
            "content": "帮我看一下悉尼的天气",
        },
    ]
    message = []
    for i in _list:
        message.append(sdk.schema.Message(**i))
    logger.debug(message)
    driver = Driver()
    logger.debug(driver)
    search = sdk.schema.Function(name="get_current_weather", description="Get the current weather")
    search.add_property(
        property_name="location",
        property_description="The city and state, e.g. San Francisco, CA",
        property_type="string",
        required=True
    )
    endpoint = openai.Openai(config=driver, messages=message, functions=[search])


    async def main():
        _result = await endpoint.create()
        logger.debug(_result)


    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logger.exception(e)
