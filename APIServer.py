from fastapi import FastAPI
from API.Signature import APISignature
from pydantic import BaseModel
from pathlib import Path
from utils.Base import ReadConfig
from App.Event import Reply
from utils.Data import Api_keys
from loguru import logger
from API.Whitelist import Whitelist
import App.Event as appe

class ReqBody(BaseModel):
    chatText: str
    chatId: int
    groupId: int
    timestamp: str
    signature: str
    
apicfg = ReadConfig().parseFile(str(Path.cwd()) + '/API/config.toml')
app = FastAPI()

@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-ExtendedAPI'}

#### Chat
@app.post('/chat')
async def chat(body: ReqBody):
    verisign = APISignature({'secret':apicfg['secret'], 'text':body.chatText, 'timestamp':body.timestamp})
    if(not verisign.verify(body.signature)):
        return {'success': False, 'response': 'SIGNATURE_MISMATCH'}
    if(not Whitelist(body, appe).checkAll()):
        return {'success': False, 'response': 'NOT_IN_WHITELIST_OR_BLOCKED'}
    try:
        if(body.chatId and body.chatText):
            res = await Reply.load_response(user=body.chatId, 
                                            group=body.groupId, 
                                            key=Api_keys.get_key()['OPENAI_API_KEY'], 
                                            prompt=body.chatText, 
                                            method='chat')
            return {'success': True, 'response': res, 'timestamp': body.timestamp}
        else:
            return {'success': False, 'response':'INVAILD_CHATINFO'}
    except Exception as e:
        logger.error(e)

#### Write
@app.post('/write')
async def write(body: ReqBody):
    verisign = APISignature({'secret':apicfg['secret'], 'text':body.chatText, 'timestamp':body.timestamp})
    if(not verisign.verify(body.signature)):
        return {'success': False, 'response': 'SIGNATURE_MISMATCH'}
    if(not Whitelist(body, appe).checkAll()):
        return {'success': False, 'response': 'NOT_IN_WHITELIST_OR_BLOCKED'}
    try:
        if(body.chatId and body.chatText):
                res = await Reply.load_response(user=body.chatId, 
                                                group=body.groupId, 
                                                key=Api_keys.get_key()['OPENAI_API_KEY'],
                                                prompt=body.chatText, 
                                                method='write')
                return {'success': True, 'response':res, 'timestamp':body.timestamp}
        else:
            return {'success': False,'response':'INVAILD_CHATINFO'}
    except Exception as e:
            logger.error(e)

#### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('APIServer:app', host='127.0.0.1', port=2333, reload=True, log_level="debug", workers=1)