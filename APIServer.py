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
from API.Voice import VITS
from utils.Chat import UserManger

class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    groupId: int = 0
    timestamp: int = 0
    signature: str = ''
    returnVoice: bool = False
    returnVoiceRaw: bool = True

if(not os.path.isfile(os.path.split(os.path.realpath(__file__))[0] + '/Config/api.toml')):
    logger.error('未检测到api.toml,请重新配置  api.toml not found, please reconfigure')
    exit()
apicfg = ReadConfig().parseFile(os.path.split(os.path.realpath(__file__))[0] + '/Config/api.toml')
config = ReadConfig().parseFile(os.path.split(os.path.realpath(__file__))[0] + '/Config/app.toml')
_csonfig = appe.load_csonfig()

def preCheck(reqbody):
    if(not _csonfig['statu']):
        return {'success': False, 'message': 'DISABLED'}
    message = FakeTGBotMessage()
    message.from_user.id = reqbody.chatId
    message.chat.id = reqbody.groupId
    verisign = APISignature({'secret':apicfg['secret'], 'text':reqbody.chatText, 'timestamp': str(reqbody.timestamp)})
    if(apicfg['doCheckSignature']):
        if(not verisign.verify(reqbody.signature)):
            return {'success': False, 'response': 'SIGNATURE_MISMATCH'}
    if(not Whitelist(_message = message, csonfig= _csonfig).checkAll()):
        return {'success': False, 'response': 'NOT_IN_WHITELIST_OR_BLOCKED'}
    if(not reqbody.chatId or not (reqbody.timestamp if apicfg['doValidateTimestamp'] else True) or not (reqbody.signature if apicfg['doCheckSignature'] else True)):
        return {'success': False,'response': 'NECESSARY_PARAMETER_IS_EMPTY'}
    if(apicfg['doValidateTimestamp']):
        if(abs(int(time.time()) - reqbody.timestamp) > apicfg['RequestTimeout']):
            return {'success': False,'response': 'TIMESTAMP_OUTDATED'}
    if(UserManger(int(reqbody.chatId)).read('voice')):
        reqbody.returnVoice = True
    # Request body is NOT ILLEGAL, so false
    return False

app = FastAPI()

# HelloWorld
@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-ExtendedAPI'}

#### Chat
@app.post('/chat')
async def chat(body: ReqBody):
    if(response := preCheck(body)):
        return response
    try:
        if(body.chatId and body.chatText):
            global res
            res = await Reply.load_response(user=body.chatId,
                                            group=body.groupId, 
                                            key=Api_keys.get_key()['OPENAI_API_KEY'], 
                                            prompt=body.chatText, 
                                            method='chat')
            if(body.returnVoice):
                vresp = await VITS.get(text = res, task = body.chatId, doReturnRawAudio=body.returnVoiceRaw)
                if(vresp):
                    return vresp
                else:
                    return {'success': True, 'response': res, 'isTTSFailed': True}
            return {'success': True, 'response': res}
        else:
            return {'success': False, 'response':'INVAILD_CHATINFO'}
    except Exception as e:
        logger.error(e)

#### Write
@app.post('/write')
async def write(body: ReqBody):
    if(response := preCheck(body)):
        return response
    try:
        if(body.chatId and body.chatText):
            global res
            res = await Reply.load_response(user=body.chatId, 
                                            group=body.groupId, 
                                            key=Api_keys.get_key()['OPENAI_API_KEY'],
                                            prompt=body.chatText,                                                 
                                            method='write',
                                            web_enhance_server=config['Enhance_Server'])
            if(body.returnVoice):
                vresp = await VITS.get(text = res, task = body.chatId, doReturnRawAudio=body.returnVoiceRaw)
                if(vresp):
                    return vresp
                else:
                    return {'success': True, 'response': res, 'isTTSFailed': True}
            return {'success': True, 'response':res}
        else:
            return {'success': False,'response':'INVAILD_CHATINFO'}
    except Exception as e:
            logger.error(e)

#### Voice
@app.post('/voice')
async def voice(body: ReqBody):
    if(response := preCheck(body)):
        return response
    try:
        user = UserManger(int(body.chatId))
        doUserVoice = False if user.read('voice') else True
        user.save({'voice': doUserVoice})
        return {'success': True, 'response': 'TTS Status: ' + str(doUserVoice)}
    except Exception as e:
        logger.error(e)
        
#### Forget
@app.post('/forgetme')
async def forgetme(body: ReqBody):
    try:
        if(response := preCheck(body)):
            return response
        message = FakeTGBotMessage()
        message.from_user.id = body.chatId
        message.chat.id = body.groupId
        if(await appe.Forget(bot = FakeTGBot(), message = message, config = config)):
            return {'success': True,'response': 'done'}
        else:
            return {'success': False,'response': 'GENERAL_FAILURE'}
    except Exception as e:
        logger.error(e)

#### Remind
@app.post('/remind')
async def remind(body: ReqBody):
    try:
        if(response := preCheck(body)):
            return response
        if(not body.chatText):
            return {'success': False,'response': 'INVAILD_CHATINFO'}
        _remind = body.chatText
        if Utils.tokenizer(_remind) > 333:
            return {'success': False, 'response': 'REMIND_TEXT_TOO_LONG'}
        if _csonfig["allow_change_head"]:
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
    except Exception as e:
        logger.error(e)

#### Administration
@app.post('/admin/{action}')
async def admin(body: ReqBody, action: str):
    try:
        if(response := preCheck(body)):
            return response
        if(not body.chatId in config.bot.master):
            return {'success': False,'response': 'OPERATION_NOT_PERMITTED'}
        admin_actions = ['set_user_cold', 'set_group_cold', 'set_token_limit', 'set_input_limit', 'see_api_key', 'del_api_key', 'add_api_key', 'set_per_user_limit', 'set_per_hour_limit', 'promote_user_limit', 'reset_user_usage', 'add_block_group', 'del_block_group', 'add_block_user', 'del_block_user', 'add_white_group', 'add_white_user', 'del_white_group', 'del_white_user', 'update_detect','open_user_white_mode', 'open_group_white_mode', 'close_user_white_mode', 'close_group_white_mode', 'open', 'close', 'disable_change_head', 'enable_change_head']
        if(not action in admin_actions):
            return {'success': False,'response': 'INVAILD_ADMIN_ACTION'}
        message = FakeTGBotMessage()
        message.from_user.id = body.chatId
        message.text = '/{action}{msg}'.format(action=action, msg=' ' + body.chatText if body.chatText else '')
        resp = {}
    
        def admin_callback(message, text):  # bot管理接口回调
            nonlocal resp
            # logger.info(text)
            # logger.info('callback executed')
            resp = {'success': True,'response': text}
    
        # bot = FakeTGBot()
        bot = FakeTGBot(reply_to_callback = admin_callback)
        await appe.Master(bot, message, config.bot)
        if(resp == {}):
            return {'success': False,'response': 'GENERAL_FAILURE'}
        return resp
    except Exception as e:
        logger.error(e)


#### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('APIServer:app', host=apicfg['uvicorn_host'], port=apicfg['uvicorn_port'], reload=apicfg['uvicorn_reload'], log_level=apicfg['uvicorn_loglevel'], workers=apicfg['uvicorn_workers'])