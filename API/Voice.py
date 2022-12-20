import sys
sys.path.append('..')
from utils.Data import TTS_REQ, TTS_Clint, Service_Data
from openai_async.utils.Talk import Talk
from fastapi.responses import Response

class VTIS:
    def get(text, task:int = 1, doReturnRawAudio: bool = True):
        serviceCfg = Service_Data.get_key('./Config/service.json')
        ttsConf = serviceCfg['tts']
        if(Talk.get_language(text) != 'chinese'):
            return False
        newtext = '[ZH]' + text + '[ZH]'
        reqbody = TTS_REQ(model_name = ttsConf['model_name'],
                          task_id = task,
                          text = newtext,
                          speaker_id = ttsConf['speaker_id'])
        data = TTS_Clint.request_tts_server(url = ttsConf['api'], params = reqbody)
        if(not data):
            return False
        if(doReturnRawAudio):
            return Response(content = TTS_Clint.decode_wav(data['audio']), media_type = 'audio/x-pcm')
        else:
            return {'success': True, 'response': data['audio'], 'text': text}