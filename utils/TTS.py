# -*- coding: utf-8 -*-
# @Time    : 12/20/22 12:37 PM
# @FileName: TTS.py
# @Software: PyCharm
# @Github    ：sudoskys
import httpx
from pydantic import BaseModel


class TTS_REQ(BaseModel):
    model_name: str = ""
    task_id: int = 1
    text: str = "[ZH]你好[ZH]"
    speaker_id: int = 0


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
    def request_azure_server(text):

        pass

    @staticmethod
    def request_vits_server(url: str, params: TTS_REQ):

        headers = {'Content-type': 'application/json',
                   'Accept': 'text/plain'}
        data = params.dict()
        # 发起请求
        try:
            response = httpx.post(url, headers=headers, json=data)
            if response.status_code != 200:
                print("TTS API Outline")
                return False
            # 接收数据
            response_data = response.json()
            if response_data["code"] != 200:
                print(f"TTS API Error{response_data.get('msg')}")
                return False
            return response_data
        except Exception as e:
            print(e)
            return False
