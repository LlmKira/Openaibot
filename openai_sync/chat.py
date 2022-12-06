# -*- coding: utf-8 -*-
# @Time    : 12/6/22 12:02 PM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys
from openai_sync import Completion


class Chatbot(object):
    def __init__(self, api_key, conversation_id):
        self._api_key = api_key
        self.conversation_id = conversation_id

    def reset_chat(self):
        # Forgets conversation
        pass

    def refresh_session(self):
        # Uses the session_token to get a new bearer token
        pass

    def get_chat_response(self):
        start_sequence = "\nAI:"
        restart_sequence = "\nHuman: "
        response = Completion(api_key=self._api_key).create(
            model="text-davinci-003",
            prompt="The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, "
                   "and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I "
                   "help you today?\nHuman: ",
            temperature=0.9,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=["Human:", "AI:"],
        )
        print(response)
