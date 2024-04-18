from typing import List

from fast_langdetect import parse_sentence
from loguru import logger

from llmkira.extra.voice import request_cn, request_en
from llmkira.kv_manager.env import EnvManager
from llmkira.kv_manager.file import File
from llmkira.openapi.hook import resign_hook, Hook, Trigger
from llmkira.sdk.utils import Ffmpeg
from llmkira.task.schema import EventMessage, Location


def check_string(text):
    """
    检查字符串是否符合要求
    :param text: 字符串
    :return: 是否符合要求
    """
    parsed_text = parse_sentence(text)
    if not parsed_text:
        return False
    lang_kinds = []
    for lang in parsed_text:
        if lang.get("lang", "RU") not in ["ZH", "EN"]:
            return False
        lang_kinds.append(lang.get("lang"))
    limit = 200
    if len(set(lang_kinds)) == 1:
        if lang_kinds[0] in ["EN"]:
            limit = 500
    if "\n\n" in text or text.count("\n") > 3 or len(text) > limit or "```" in text:
        return False
    return True


@resign_hook()
class VoiceHook(Hook):
    trigger: Trigger = Trigger.RECEIVER

    async def trigger_hook(self, *args, **kwargs) -> bool:
        platform_name: str = kwargs.get("platform")  # noqa
        messages: List[EventMessage] = kwargs.get("messages")
        locate: Location = kwargs.get("locate")
        for message in messages:
            if not check_string(message.text):
                return False
        have_env = await EnvManager(locate.uid).get_env("VOICE_REPLY_ME", None)
        # logger.warning(f"Voice Hook {have_env}")
        if have_env is not None:
            return True
        return False

    async def hook_run(self, *args, **kwargs):
        logger.debug(f"Voice Hook {args} {kwargs}")
        platform_name: str = kwargs.get("platform")  # noqa
        messages: List[EventMessage] = kwargs.get("messages")
        locate: Location = kwargs.get("locate")
        for message in messages:
            if not check_string(message.text):
                return args, kwargs
            parsed_text = parse_sentence(message.text)
            if not parsed_text:
                return args, kwargs
            lang_kinds = []
            for lang in parsed_text:
                lang_kinds.append(lang.get("lang"))
            reecho_api_key = await EnvManager(locate.uid).get_env(
                "REECHO_VOICE_KEY", None
            )
            if (len(set(lang_kinds)) == 1) and (lang_kinds[0] in ["EN"]):
                voice_data = await request_en(message.text)
            else:
                voice_data = await request_cn(
                    message.text, reecho_api_key=reecho_api_key
                )
            if voice_data is not None:
                ogg_data = Ffmpeg.convert(
                    input_c="mp3", output_c="ogg", stream_data=voice_data, quiet=True
                )
                file = await File.upload_file(
                    creator=locate.uid, file_name="speech.ogg", file_data=ogg_data
                )
                file.caption = message.text
                message.text = ""
                message.files.append(file)
            else:
                logger.error(f"Voice Generation Failed:{message.text}")
        return args, kwargs
