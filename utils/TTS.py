# -*- coding: utf-8 -*-
# @Time    : 12/20/22 12:37 PM
# @FileName: TTS.py
# @Software: PyCharm
# @Github    ：sudoskys

import random

from pydantic import BaseModel

from utils.Network import NetworkClient


class TTS_REQ(BaseModel):
    model_name: str = ""
    task_id: int = 1
    text: str = "[ZH]你好[ZH]"
    speaker_id: int = 0
    audio_type: str = "ogg"


class TTS_Clint(object):
    @staticmethod
    def decode_wav(encoded_data):
        import base64
        try:
            decoded_data = base64.b64decode(encoded_data)
            return decoded_data
        except Exception:
            return None

    @staticmethod
    async def request_azure_server(key, location: str, text: str, speaker: str):
        _key = key
        if isinstance(key, list):
            # 增强负载能力
            _key = random.choice(key)
        if not _key:
            return False, "Azure Key Empty"
        try:
            result = await Azure_TTS(key=_key, location=location).get_speech(text=text, speaker=speaker)
        except Exception as e:
            return False, e
        else:
            return result, ""

    @staticmethod
    async def request_vits_server(url: str, params: TTS_REQ):
        """
        接收配置中的参数和构造的数据类，返回字节流
        :param url:
        :param params:
        :return:
        """
        # 发起请求
        try:
            result = await VITS_TTS(url=url).get_speech(params=params)
        except Exception as e:
            return False, e
        try:
            data = TTS_Clint.decode_wav(result["audio"])
        except Exception as e:
            return False, e
        else:
            return data, ""


class VITS_TTS(object):
    def __init__(self, url, timeout: int = 30, proxy: str = None):
        self.__url = url
        self.__client = NetworkClient(timeout=timeout, proxy=proxy)

    async def get_speech(self, params: TTS_REQ):
        """
        返回 json
        :param params:
        :return:
        """
        headers = {'Content-type': 'application/json',
                   'Accept': 'text/plain'}
        data = params.json()
        response = await self.__client.request(method="POST",
                                               url=self.__url,
                                               data=data,
                                               headers=headers,
                                               )
        if response.status_code != 200:
            print("TTS API Outline")
            return False
        # 接收数据
        response_data = response.json()
        if response_data["code"] != 200:
            print(f"TTS API Error{response_data.get('msg')}")
            return False
        return response_data


class Azure_TTS(object):
    def __init__(self, key: str, location: str, timeout: int = 30, proxy: str = None):
        """
        Azure TTS 类型
        :param key: api 密钥
        :param location: 服务器组
        :param timeout: 超时
        :param proxy: 代理
        """
        self.__location = location
        self.__key = key
        self.__client = NetworkClient(timeout=timeout, proxy=proxy)

    async def get_voice_list(self):
        req = await self.__client.request(method="GET",
                                          url="https://{}.tts.speech.microsoft.com/cognitiveservices/voices/list".format(
                                              self.__location),
                                          headers={"Ocp-Apim-Subscription-Key": self.__key},
                                          )
        return req

    async def get_speech(self, text: str, speaker: str):
        """
        返回数据流
        :param text: 文本
        :param speaker: 发言人
        :return:
        """
        headers = {
            "Ocp-Apim-Subscription-Key": self.__key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-96kbitrate-mono-mp3",
            "User-Agent": "curl",
        }
        data_raw = """<speak version='1.0' xml:lang='en-US'><voice xml:lang='en-US' xml:gender='Female' name='{}'>{}</voice></speak>""".format(
            speaker, text
        )
        url = "https://{}.tts.speech.microsoft.com/cognitiveservices/v1".format(
            self.__location
        )
        req = await self.__client.request(method="POST",
                                          url=url,
                                          headers=headers,
                                          data=data_raw,
                                          )
        req.raise_for_status()
        return req.read()
