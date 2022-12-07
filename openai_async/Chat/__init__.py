# -*- coding: utf-8 -*-
# @Time    : 12/6/22 12:02 PM
# @FileName: chat.py
# @Software: PyCharm
# @Github    ：sudoskys

# 基于 Completion 上层
from openai_async import Completion
from ..utils.data import MsgFlow


class Chatbot(object):
    def __init__(self, api_key, conversation_id, call_func=None):
        """
        chatGPT 的实现由上下文实现，所以我会做一个存储器来获得上下文
        :param api_key:
        :param conversation_id: 独立ID,每个场景需要独一个
        :param call_func: 回调
        """
        self._api_key = api_key
        self.conversation_id = conversation_id
        self._MsgFlow = MsgFlow(uid=self.conversation_id)
        self._start_sequence = "\nGirl:"
        self._restart_sequence = "\nHuman: "
        self.__call_func = call_func

    def reset_chat(self):
        # Forgets conversation
        return self._MsgFlow.forget()

    def record_ai(self, prompt, response):
        REPLY = []
        Choice = response.get("choices")
        if Choice:
            for item in Choice:
                _text = item.get("text")
                REPLY.append(_text)
        if not REPLY:
            REPLY = ["(Ai Say Nothing)"]
        self._MsgFlow.save(prompt=prompt, role=self._restart_sequence)
        self._MsgFlow.save(prompt=REPLY[0], role=self._start_sequence)
        return REPLY

    @staticmethod
    def random_string(length):
        import string  # 导入string模块
        import random  # 导入random模块

        all_chars = string.ascii_letters + string.digits  # 获取所有字符，包括大小写字母和数字

        result = ''  # 创建一个空字符串用于保存生成的随机字符

        for i in range(length):
            result += random.choice(all_chars)  # 随机选取一个字符，并添加到result中

        return result  # 返回生成的随机字符

    # _prompt = random_string(3700)

    def get_hash(self):
        import hashlib
        my_string = str(self.conversation_id)
        # 使用 hashlib 模块中的 sha256 算法创建一个散列对象
        hash_object = hashlib.sha256(my_string.encode())
        return hash_object.hexdigest()

    async def get_chat_response(self, prompt: str, max_tokens: int = 150, model: str = "text-davinci-003",
                                character: list = None, head: str = None) -> dict:
        """
        异步的，得到对话上下文
        :param head: 预设技巧
        :param max_tokens: 限制返回字符数量
        :param model: 模型选择
        :param prompt: 提示词
        :param character: 性格提示词，列表字符串
        :return:
        """
        if head is None:
            head = f"\nHuman: 你好，你是谁？\nAI: 我是 Ai assistant 请提问?"
        if character is None:
            character = ["helpful", "creative", "clever", "friendly", "lovely"]
        _character = ",".join(character)
        _now = f"{self._restart_sequence}{prompt}."
        # 构建 prompt 上下文，由上下文桶提供支持
        _old = self._MsgFlow.read()
        _head = f"The following is a conversation with Ai assistant. The assistant is {_character}."
        _head = f"{_head}\n{head}\n"
        # 截断器
        _old_list = [f"{x['role']} {x['prompt']}" for x in _old]
        total_length = 0
        cutoff_index = -1
        for i in reversed(range(len(_old_list))):
            string_length = len(_old_list[i])
            total_length += string_length
            # 检查总长度是否超过了限制
            if total_length > 3800:
                cutoff_index = i
                break
        _old_list = _old_list[:cutoff_index]
        _old_prompt = '\n'.join(_old_list)  # 首个不带 \n
        _prompt = f"{_head}{_old_prompt}{_now}\n{self._start_sequence}"
        _prompt = _prompt[:3800]
        response = await Completion(api_key=self._api_key, call_func=self.__call_func).create(
            model=model,
            prompt=_prompt,
            temperature=0.9,
            max_tokens=max_tokens,
            top_p=1,
            n=1,
            frequency_penalty=0,
            presence_penalty=0.5,
            user=str(self.get_hash()),
            stop=["Human:", "AI:"],
        )
        self.record_ai(prompt=prompt, response=response)
        return response
