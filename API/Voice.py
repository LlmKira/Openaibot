import sys
sys.path.append('..')
from utils.Data import Service_Data
from utils.TTS import VITS_TTS, TTS_REQ, TTS_Clint
from openai_async.utils.Talk import Talk
from fastapi.responses import Response
from loguru import logger
from ftlangdetect import detect

serviceCfg = Service_Data.get_key('./Config/service.json')
ttsConf = serviceCfg['tts']

class VITS:
    async def vits(text, task:int = 1, doReturnRawAudio: bool = True):
        vitsConf = ttsConf['vits']
        lang = detect(text=text.replace("\n", "").replace("\r", ""), low_memory=True).get("lang").upper()
        if( lang not in ["ZH", "JA"]):
            logger.warning('语言不支持。语音合成目前仅支持合成中文、日语')
            return False
        text = Talk.chinese_sentence_cut(text)
        cn = {i: f"[{lang}]" for i in text}
        _spell = [f"{cn[x]}{x}{cn[x]}" for x in cn.keys()]
        newtext = "".join(_spell)
        newtext = "[LENGTH]1.4[LENGTH]" + newtext
        reqbody = TTS_REQ(model_name = vitsConf['model_name'],
                          task_id = task,
                          text = newtext,
                          speaker_id = vitsConf['speaker_id'])
        data,e = await VITS_TTS.get_speech(url = vitsConf['api'], params = reqbody)
        if(not data):
            logger.warning(e)
            return False
        if(doReturnRawAudio):
            return Response(content = TTS_Clint.decode_wav(data['audio']), media_type = 'audio/x-pcm')
        else:
            return {'success': True, 'response': data['audio'], 'text': text}
    async def azure(self, text, doReturnRawAudio:bool = False):
        azureConf = ttsConf['azure']
        lang = detect(text=text.replace("\n", "").replace("\r", ""), low_memory=True).get("lang").upper()
        speaker = azureConf["speaker"].get(lang)
        if(not speaker):
            logger.warning('语言不支持。语音合成目前仅支持合成中文、日语')
            return False
        resp,e = await TTS_Clint.request_azure_server(key = azureConf['key'],
                                                      location = azureConf['location'],
                                                      text = text,
                                                      speaker = speaker)
        if(not resp):
            logger.warning(e)
            return False
        if(doReturnRawAudio):
            return Response(content = resp, media_type = 'audio/x-pcm')
        else:
            import base64
            base64audio = base64.b64encode(resp)
            return {'success': True,'response': base64audio, 'text': text}
        
    async def get(self, text, task:int = 1, doReturnRawAudio:bool = True):
        ttsType = ttsConf['type']
        if(ttsType == 'vits'):
            return await VITS.vits(text, task, doReturnRawAudio)
        elif(ttsType == 'azure'):
            return await VITS.azure(text, doReturnRawAudio)
        else:
            return False