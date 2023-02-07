import os
import time

from fastapi import FastAPI
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel

import App.Event as appe
from API.Signature import APISignature
from utils import Setting
from utils.Base import ReadConfig
from utils.Data import create_message, PublicReturn


class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    chatName: str = 'Master'
    groupId: int = -1
    timestamp: int = -1
    signature: str = ''
    returnVoice: bool = True


apicfg = ReadConfig().parseFile(os.path.split(os.path.realpath(__file__))[0] + '/Config/api.toml')
_csonfig = appe.load_csonfig()
ProfileManager = Setting.ProfileManager()


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


def newMsg(body: ReqBody, type_name):
    isGroup: bool = True
    gid: int = body.groupId
    if body.groupId == -1:
        isGroup = False
        gid = body.chatId
    msgObj = create_message(user_id=body.chatId,
                            user_name=body.chatName,
                            group_id=gid,
                            text=f'/{type_name} {body.chatText}',
                            state=103,
                            group_name='')
    return {'msgObj': msgObj, 'isGroup': isGroup}


app = FastAPI()


# HelloWorld
@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-HTTPAPI'}


@app.post('/{command}')
async def universalHandler(command=None, body: ReqBody = None):
    if command is None:
        command = ['chat', 'write', 'voice', 'forgetme', 'remind']
    not_valid = preCheck(body)
    if not_valid:  # 预检查错误信息
        return not_valid
    msg = newMsg(body, command)
    resp: PublicReturn
    finalMsg: str

    if msg['isGroup']:
        resp = await appe.Group(Message=msg['msgObj'], bot_profile=ProfileManager.access_api(init=False), config=apicfg)
    else:
        resp = await appe.Friends(Message=msg['msgObj'], bot_profile=ProfileManager.access_api(init=False),
                                  config=apicfg)

    finalMsg = resp.reply if resp.reply else resp.msg
    if not resp.status:  # 不成功
        return {'success': False, 'response': 'GENERAL_FAILURE'}
    if resp.voice and body.returnVoice:  # 语音正常、请求语音返回
        import base64
        httpRes = Response(content=resp.voice, media_type='audio/ogg')
        httpRes.headers['X-Bot-Reply'] = str(base64.b64encode(resp.reply.encode('utf-8')), 'utf-8')
        return httpRes
    return {'success': True, 'response': finalMsg}


#### Administration
@app.post('/admin/{action}')
async def admin(body: ReqBody, action: str):
    try:
        not_valid = preCheck(body)
        if not_valid:
            return not_valid
        if body.chatId not in apicfg.master:
            return {'success': False, 'response': 'OPERATION_NOT_PERMITTED'}
        admin_actions = ['set_user_cold', 'set_group_cold', 'set_token_limit', 'set_input_limit', 'see_api_key',
                         'del_api_key', 'add_api_key', 'set_per_user_limit', 'set_per_hour_limit', 'promote_user_limit',
                         'reset_user_usage', 'add_block_group', 'del_block_group', 'add_block_user', 'del_block_user',
                         'add_white_group', 'add_white_user', 'del_white_group', 'del_white_user', 'update_detect',
                         'open_user_white_mode', 'open_group_white_mode', 'close_user_white_mode',
                         'close_group_white_mode', 'open', 'close', 'change_head', 'change_style', 'auto_adjust']
        if action not in admin_actions:
            return {'success': False, 'response': 'INVAILD_ADMIN_ACTION'}
        msg = newMsg(body, action)
        resp = await appe.MasterCommand(user_id=body.chatId, Message=msg['msgObj'], pLock=None, config=apicfg)
        if not resp:
            return {'success': False, 'response': 'GENERAL_FAILURE'}
        return {'success': True, 'response': resp[0]}
    except Exception as e:
        logger.error(e)


#### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn

    ProfileManager.access_api(bot_name=apicfg.botname[:6], bot_id=apicfg.botid, init=True)
    uvicorn.run('APIServer:app', host=apicfg['uvicorn_host'], port=apicfg['uvicorn_port'],
                reload=False, log_level=apicfg['uvicorn_loglevel'],
                workers=apicfg['uvicorn_workers'])
