# -*- coding: utf-8 -*-
# @Time    : 12/6/22 10:23 AM
# @FileName: chatGPT.py
# @Software: PyCharm
# @Github    ：sudoskys

# 自己打包的utils 库，调用自己打包的 Gpt api

from openai_async.Chat import Chatbot
from utils.Data import DataWorker

# 工具数据类型
ConversionUtils = DataWorker(prefix="Open_Ai_bot_chat_")


class ChatUtils(object):
    def __init__(self, user, api_key):
        self._api_key = api_key
        self.user = user
        self.conversation_id = ConversionUtils.getKey(self.user)
        if not self.conversation_id:
            self.conversation_id = None
        self.chatbot = Chatbot(api_key=self._api_key, conversation_id=self.conversation_id)

    def _renew_conversation_id(self, conversation_id):
        ConversionUtils.setKey(self.user, conversation_id)

    def get_resp(self, prompt: str = "test", output: str = "text"):
        try:
            resp = self.chatbot.get_chat_response(prompt,
                                                  output=output)
            # Sends a request to the API and returns the response by OpenAI
            # The current conversation id
            response_id = resp['parent_id']  # The ID of the response
            self._renew_conversation_id(resp['conversation_id'])
            message = resp['message']  # The message sent by the response
        except Exception as e:
            return {"status": False, "message": e, "response_id": None}
        else:
            return {"status": True, "message": message, "response_id": response_id}


class PrivateChat(object):

    @staticmethod
    async def load_response(user, group, key: str = "", prompt: str = "Say this is a test",
                            userlimit: int = None):
        userChatObj = ChatUtils(user=user)
        rep = userChatObj.get_resp(prompt=prompt, output="text")
        return rep
