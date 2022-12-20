import sys
sys.path.append('..')
from utils.Data import TTS_REQ, TTS_Clint, Service_Data
from openai_async.utils.Talk import Talk
from fastapi.responses import Response
from loguru import logger

serviceCfg = Service_Data.get_key('./Config/service.json')
ttsConf = serviceCfg['tts']

class VITS:
    def vits(text, task:int = 1, doReturnRawAudio: bool = True):
        vitsConf = ttsConf['vits']
        if(Talk.get_language(text) != 'chinese'):
            logger.warning('语言不支持。语音合成目前仅支持合成中文')
            return False
        newtext = '[ZH]' + text + '[ZH]'
        reqbody = TTS_REQ(model_name = vitsConf['model_name'],
                          task_id = task,
                          text = newtext,
                          speaker_id = vitsConf['speaker_id'])
        data = TTS_Clint.request_tts_server(url = vitsConf['api'], params = reqbody)
        if(not data):
            logger.warning('语言合成服务请求失败')
            return False
        if(doReturnRawAudio):
            return Response(content = TTS_Clint.decode_wav(data['audio']), media_type = 'audio/x-pcm')
        else:
            return {'success': True, 'response': data['audio'], 'text': text}
    def get(self, text, task:int = 1, doReturnRawAudio:bool = True):
        ttsType = ttsConf['type']
        if(ttsType == 'vits'):
            return VITS().vits(text, task, doReturnRawAudio)
        else:
            return {}  #留个空