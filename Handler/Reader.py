# -*- coding: utf-8 -*-
# @Time    : 1/30/23 11:01 AM
# @FileName: Reader.py
# @Software: PyCharm
# @Github    ：sudoskys
import PIL.Image
import piexif
import piexif.helper
import json
import pathlib
from typing import Optional
from loguru import logger

# 调用基础单元
from utils.Network import NetworkClient


class FileReader(object):
    async def get_ai_image_info(self, image_path):
        if not pathlib.Path(image_path).exists():
            return
        image = PIL.Image.open(image_path)
        _image_info = image.info or {}
        _gen_info = _image_info.pop('parameters', None)
        if "exif" in _image_info:
            exif = piexif.load(_image_info["exif"])
            exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
            try:
                exif_comment = piexif.helper.UserComment.load(exif_comment)
            except ValueError:
                exif_comment = exif_comment.decode('utf8', errors="ignore")
            if exif_comment:
                _image_info['exif comment'] = exif_comment
                _gen_info = exif_comment
            for field in ['jfif', 'jfif_version', 'jfif_unit',
                          'jfif_density', 'dpi', 'exif',
                          'loop', 'background', 'timestamp',
                          'duration']:
                _image_info.pop(field, None)
        if _image_info.get("Software", None) == "NovelAI":
            try:
                json_info = json.loads(_image_info["Comment"])
                _gen_info = f"""{_image_info["Description"]}
Negative prompt: {json_info["uc"]},
Steps: {json_info["steps"]},
CFG scale: {json_info["scale"]},
Seed: {json_info["seed"]},
Size: {image.width}x{image.height}
"""
            except Exception as e:
                pass
        return _gen_info


class BlipServer(object):
    def __init__(self, api: str):
        if not api.rstrip("/").endswith("upload"):
            api = api.rstrip("/") + "/upload/"
        self._url = api

    async def generate_caption(self, image_path: str) -> Optional[str]:
        if not pathlib.Path(image_path).exists():
            return
        try:
            response = await BlipRequest(url=self._url).get(file=image_path)
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
