from fastapi import FastAPI
from API.Signature import APISignature
from pydantic import BaseModel
from utils.Base import ReadConfig
from App.Event import Reply
from utils.Data import Api_keys
from loguru import logger
from API.Whitelist import Whitelist
from utils.Chat import Header, Utils
import App.Event as appe
import time
import os
from API.FakeMessage import FakeTGBotMessage, FakeTGBot

class ReqBody(BaseModel):
    chatText: str
    chatId: int
    groupId: int
    timestamp: int
    signature: str
    
apicfg = ReadConfig().parseFile(os.path.split(os.path.realpath(__file__))[0] + '/API/config.toml')
config = ReadConfig().parseFile(os.path.split(os.path.realpath(__file__))[0] + '/Config/app.toml')
_csonfig = appe.load_csonfig()

app = FastAPI()

@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-ExtendedAPI'}

def checkIllegal(reqbody):
    message = FakeTGBotMessage()
    message.from_user.id = reqbody.chatId
    message.chat.id = reqbody.groupId
    verisign = APISignature({'secret':apicfg['secret'], 'text':reqbody.chatText, 'timestamp': str(reqbody.timestamp)})
    if(not verisign.verify(reqbody.signature)):
        return {'success': False, 'response': 'SIGNATURE_MISMATCH'}
    if(not Whitelist(_message = message, csonfig= _csonfig).checkAll()):
        return {'success': False, 'response': 'NOT_IN_WHITELIST_OR_BLOCKED'}
    if(not reqbody.chatId or not reqbody.timestamp or not reqbody.signature):
        return {'success': False,'response': 'NECESSARY_PARAMETER_IS_EMPTY'}
    '''
    if(abs(int(time.time()) - reqbody.timestamp) > 3600):
        return {'success': False,'response': 'TIMESTAMP_OUTDATED'}
    '''
    return False

#### Chat
@app.post('/chat')
async def chat(body: ReqBody):
    if(response := checkIllegal(body)):
        return response
    try:
        if(body.chatId and body.chatText):
            res = await Reply.load_response(user=body.chatId, 
                                            group=body.groupId, 
                                            key=Api_keys.get_key()['OPENAI_API_KEY'], 
                                            prompt=body.chatText, 
                                            method='chat')
            return {'success': True, 'response': res}
        else:
            return {'success': False, 'response':'INVAILD_CHATINFO'}
    except Exception as e:
        logger.error(e)

#### Write
@app.post('/write')
async def write(body: ReqBody):
    if(response := checkIllegal(body)):
        return response
    try:
        if(body.chatId and body.chatText):
                res = await Reply.load_response(user=body.chatId, 
                                                group=body.groupId, 
                                                key=Api_keys.get_key()['OPENAI_API_KEY'],
                                                prompt=body.chatText, 
                                                method='write')
                return {'success': True, 'response':res}
        else:
            return {'success': False,'response':'INVAILD_CHATINFO'}
    except Exception as e:
            logger.error(e)

#### Forget
@app.post('/forgetme')
async def forgetme(body: ReqBody):
    if(response := checkIllegal(body)):
        return response
    message = FakeTGBotMessage()
    message.from_user.id = body.chatId
    message.chat.id = body.groupId
    try:
        if(appe.Forget(message = message)):
            return {'success': True,'response': 'done'}
        else:
            return {'success': False,'response': 'GENERAL_FAILURE'}
    except Exception as e:
        logger.error(e)

#### Remind
@app.post('/remind')
async def remind(body: ReqBody):
    if(response := checkIllegal(body)):
        return response
    if Utils.tokenizer(_remind) > 333:
        return {'success': False, 'response': 'REMIND_TEXT_TOO_LONG'}
    if _csonfig["allow_change_head"]:
        _remind = body.chatText
        # _remind = _remind.replace("你是", "ME*扮演")
        _remind = _remind.replace("你", "ME*")
        _remind = _remind.replace("我", "YOU*")
        _remind = _remind.replace("YOU*", "你")
        _remind = _remind.replace("ME*", "我")
        if(Header(uid=body.chatId).set(_remind)):
            return {'success': True,'response': '设定完成：' + _remind}
        else:
            return {'success': False,'response': 'GENERAL_FAILURE'}
    else:
        Header(uid=body.chatId).set({})
        return {'success': False, 'response': 'REMIND_COMMAND_PROHIBITED'}

#### Administration
@app.post('/admin/{action}')
async def admin(body: ReqBody, action: str):
    if(response := checkIllegal(body)):
        return response
    if(not body.chatId in config.master):
        return {'success': False,'response': 'OPERATION_NOT_PERMITTED'}
    admin_actions = ['set_user_cold', 'set_group_cold', 'set_token_limit', 'set_input_limit', 'see_api_key', 'del_api_key', 'add_api_key', 'set_per_user_limit', 'set_per_hour_limit', 'promote_user_limit', 'reset_user_usage', 'add_block_group', 'del_block_group', 'add_block_user', 'del_block_user', 'add_white_group', 'add_white_user', 'del_white_group', 'del_white_user', 'update_detect','open_user_white_mode', 'open_group_white_mode', 'close_user_white_mode', 'close_group_white_mode', 'open', 'close', 'disable_change_head', 'enable_change_head']
    if(not action in admin_actions):
        return {'success': False,'response': 'INVAILD_ADMIN_ACTION'}
    message = FakeTGBotMessage()
    message.from_user.id = body.chatId
    message.text = '/{action} {msg}'.format(action=action, msg=body.chatText)
    '''
    def admin_callback(message, text):  # bot接口回调
        return {'success': True,'response': text}
    '''
    bot = FakeTGBot()
    await appe.Master(bot, message, config)
    return {'success': True,'response': bot.resp}

#### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('APIServer:app', host='127.0.0.1', port=2333, reload=True, log_level="debug", workers=1)