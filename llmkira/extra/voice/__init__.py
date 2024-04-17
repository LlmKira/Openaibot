import base64
import json

import aiohttp


async def request_cn_speech(text):
    """
    Call the DuerOS endpoint to generate synthesized voice.
    :param text: The text to synthesize
    :return: The synthesized voice audio data
    """
    base_url = "https://dds.dui.ai/runtime/v1/synthesize"
    params = {
        "voiceId": "hchunf_ctn",
        "text": text,
        "speed": "1",
        "volume": "50",
        "audioType": "wav",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if (
                response.status != 200
                or response.headers.get("Content-Type") != "audio/wav"
            ):
                return None
            return await response.read()


def get_audio_bytes_from_data_url(data_url):
    """
    Extract audio bytes from a Data URL.

    Parameters:
        data_url (str): A Data URL containing base64 encoded audio.

    Returns:
        bytes: The extracted audio data if the extraction is successful, otherwise None.
    """
    try:
        audio_base64 = data_url.split(",")[1]
        audio_bytes = base64.b64decode(audio_base64)
        return audio_bytes
    except Exception:
        return None


async def request_reecho_speech(
    text: str, reecho_api_key: str, voiceId="eb5d7f8c-eea1-483f-b718-1f28d6649339"
):
    """
    Call the Reecho endpoint to generate synthesized voice.
    :param text: The text to synthesize
    :param voiceId: The voiceId to use
    :param reecho_api_key: The Reecho API token
    :return: The synthesized voice audio data, or None if the request failed
    """
    if not reecho_api_key:
        return await request_cn_speech(text)
    url = "https://v1.reecho.ai/api/tts/simple-generate"
    headers = {
        "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {reecho_api_key}",  # Replace {token} with your Reecho API token
    }
    data = {"voiceId": voiceId, "text": text, "origin_audio": True}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=json.dumps(data)
        ) as response:
            if response.status == 200:
                response_json = await response.json()
                audio_url = response_json["data"].get("audio", None)
                audio_bytes = get_audio_bytes_from_data_url(audio_url)
    if not audio_bytes:
        return await request_cn_speech(text)
    return audio_bytes


async def request_en_speech(text):
    """
    Call the NovelAI endpoint to generate synthesized voice.
    :param text: The text to synthesize
    :return: The synthesized voice audio data
    """
    base_url = "https://api.novelai.net/ai/generate-voice"
    headers = {"accept": "*/*"}
    params = {
        "text": text,
        "seed": "Claea",
        "voice": "-1",
        "opus": "false",
        "version": "v2",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params, headers=headers) as response:
            if response.status != 200:
                return None
            audio_content_type = response.headers.get("Content-Type")
            valid_content_types = ["audio/mpeg", "audio/ogg", "audio/opus"]
            if audio_content_type not in valid_content_types:
                return None
            return await response.read()
