from fastapi import FastAPI
from fastapi.responses import Response
from API.Signature import APISignature
from pydantic import BaseModel
from utils.Base import ReadConfig
from utils.Data import create_message, PublicReturn
from loguru import logger
import App.Event as appe
import time
import os
from API.FakeMessage import FakeTGBotMessage, FakeTGBot
from typing import Union


class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    chatName: str
    groupId: int = -1
    timestamp: int = -1
    signature: str = ''
    returnVoice: bool = False
    returnVoiceRaw: bool = True
    chatName: str = ""
    audioFormat: str = Union['wav', 'ogg', 'flac']


apicfg = ReadConfig().parseFile(os.path.split(os.path.realpath(__file__))[0] + '/Config/api.toml')
_csonfig = appe.load_csonfig()


def preCheck(reqbody):
    verisign = APISignature({'secret': apicfg['secret'], 'text': reqbody.chatText, 'timestamp': str(reqbody.timestamp)})
    if apicfg['doCheckSignature']:
        if not verisign.verify(reqbody.signature):
            return {'success': False, 'response': 'SIGNATURE_MISMATCH'}
    if (not reqbody.chatId or not (reqbody.timestamp if apicfg['doValidateTimestamp'] else True) or not (
            reqbody.signature if apicfg['doCheckSignature'] else True)):
        return {'success': False, 'response': 'NECESSARY_PARAMETER_IS_EMPTY'}
    if apicfg['doValidateTimestamp']:
        if abs(int(time.time()) - reqbody.timestamp) > apicfg['RequestTimeout']:
            return {'success': False, 'response': 'TIMESTAMP_OUTDATED'}
    # Request body is NOT ILLEGAL, so false
    return False


app = FastAPI()


# HelloWorld
@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-HTTPAPI'}


def newMsg(body: ReqBody, type):
    isGroup: bool = True
    gid: int = body.groupId
    if body.groupId == -1:
        isGroup = False
        gid = body.chatId
    msgObj = create_message(user_id=body.chatId,
                            user_name=body.chatName,
                            group_id=gid,
                            text=f'/{type} {body.chatText}',
                            state=103)
    return {'msgObj': msgObj, 'isGroup': isGroup}


@app.post('/{command}')
async def universalHandler(command: str=['chat', 'write', 'voice', 'forgetme', 'remind'], body: ReqBody=None):
    msg = newMsg(body, command)
    resp: PublicReturn
    finalMsg: str
    
    if msg['isGroup']:
        resp = appe.Group(msg['msgObj'], apicfg)
    else:
        resp = appe.Friends(msg['msgObj'], apicfg)
    
    finalMsg = resp.reply if resp.reply else resp.msg
    if not resp.status:  # 不成功
        return {'success': False, 'response': 'GENERAL_FAILURE', 'text': finalMsg}
    if resp.voice and body.returnVoice:  # 语音正常、请求语音返回
        return Response(content=resp.voice, media_type='audio/x-pcm')
    return {'success': True, 'response': finalMsg}
    
    
#### Administration
@app.post('/admin/{action}')
async def admin(body: ReqBody, action: str):
    try:
        response = preCheck(body)
        if response:
            return response
        if not body.chatId in config.bot.master:
            return {'success': False, 'response': 'OPERATION_NOT_PERMITTED'}
        admin_actions = ['set_user_cold', 'set_group_cold', 'set_token_limit', 'set_input_limit', 'see_api_key',
                         'del_api_key', 'add_api_key', 'set_per_user_limit', 'set_per_hour_limit', 'promote_user_limit',
                         'reset_user_usage', 'add_block_group', 'del_block_group', 'add_block_user', 'del_block_user',
                         'add_white_group', 'add_white_user', 'del_white_group', 'del_white_user', 'update_detect',
                         'open_user_white_mode', 'open_group_white_mode', 'close_user_white_mode',
                         'close_group_white_mode', 'open', 'close', 'disable_change_head', 'enable_change_head']
        if not action in admin_actions:
            return {'success': False, 'response': 'INVAILD_ADMIN_ACTION'}
        message = FakeTGBotMessage()
        message.from_user.id = body.chatId
        message.text = '/{action}{msg}'.format(action=action, msg=' ' + body.chatText if body.chatText else '')
        resp = {}

        def admin_callback(message, text):  # bot管理接口回调
            nonlocal resp
            # logger.info(text)
            # logger.info('callback executed')
            resp = {'success': True, 'response': text}

        # bot = FakeTGBot()
        bot = FakeTGBot(reply_to_callback=admin_callback)
        await appe.MasterCommand(user_id=message.from_user.id, Message=, pLock=None)
        if resp == {}:
            return {'success': False, 'response': 'GENERAL_FAILURE'}
        return resp
    except Exception as e:
        logger.error(e)


#### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn

    uvicorn.run('APIServer:app', host=apicfg['uvicorn_host'], port=apicfg['uvicorn_port'],
                reload=apicfg['uvicorn_reload'], log_level=apicfg['uvicorn_loglevel'],
                workers=apicfg['uvicorn_workers'])
