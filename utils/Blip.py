# -*- coding: utf-8 -*-
# @Time    : 1/30/23 11:01 AM
# @FileName: Blip.py
# @Software: PyCharm
# @Github    ：sudoskys
import pathlib
from typing import Optional
from loguru import logger
from utils.Network import NetworkClient


class BlipServer(object):
    def __init__(self, api: str):
        if not api.rstrip("/").endswith("upload"):
            api = api.rstrip("/") + "/upload/"
        self._url = api

    async def generate_caption(self, image_file: str) -> Optional[str]:
        if not pathlib.Path(image_file).exists():
            return
        try:
            response = await BlipRequest(url=self._url).get(file=image_file)
            _data = response["message"]
        except Exception as e:
            logger.warning(f"Blip:{e}")
            return
        else:
            return _data


class BlipRequest(object):
    def __init__(self, url, timeout: int = 30, proxy: str = None):
        self.__url = url
        self.__client = NetworkClient(timeout=timeout, proxy=proxy)

    async def get(self, file) -> dict:
        """
        返回 json
        :return:
        """
        headers = {'Accept': 'application/json'}
        response = await self.__client.request(method="POST",
                                               url=self.__url,
                                               headers=headers,
                                               files={'file': open(file, 'rb')}
                                               )
        response_data = response.json()
        if response.status_code != 200:
            logger.warning(f"Blip API Outline:{response_data.get('detail')}")
        if response_data["code"] != 1:
            logger.warning(f"Blip API Error{response_data.get('msg')}")
        return response_data
