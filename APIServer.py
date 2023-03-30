# 此文件需要重写，以适应新的API


import os
import time

from fastapi import FastAPI
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel

import App.Event as AppEvent
from Component.sign_api.Signature import APISignature
from Handler import Manager
from utils.Base import TOMLConfig
from utils.Data import create_message, PublicReturn


class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    chatName: str = 'Master'
    groupId: int = -1
    timestamp: int = -1
    signature: str = ''
    returnVoice: bool = True


api_cfg = TOMLConfig().parse_file(os.path.split(os.path.realpath(__file__))[0] + '/Config/sign_api.toml')
_config = AppEvent.load_csonfig()
ProfileManager = Manager.ProfileManager()


def pre_signature_check(reqbody):
    verisign = APISignature(
        {'secret': api_cfg['secret'], 'text': reqbody.chatText, 'timestamp': str(reqbody.timestamp)})
    if api_cfg['doCheckSignature']:
        if not verisign.verify(reqbody.signature):
            return {'success': False, 'response': 'SIGNATURE_MISMATCH'}
    if (not reqbody.chatId or not (reqbody.timestamp if api_cfg['doValidateTimestamp'] else True) or not (
            reqbody.signature if api_cfg['doCheckSignature'] else True)):
        return {'success': False, 'response': 'NECESSARY_PARAMETER_IS_EMPTY'}
    if api_cfg['doValidateTimestamp']:
        if abs(int(time.time()) - reqbody.timestamp) > api_cfg['RequestTimeout']:
            return {'success': False, 'response': 'TIMESTAMP_OUTDATED'}
    # Request body is NOT ILLEGAL, so false
    return False


def receive_message(body: ReqBody, type_name):
    is_group: bool = True
    gid: int = body.groupId
    if body.groupId == -1:
        is_group = False
        gid = body.chatId
    msg = create_message(user_id=body.chatId,
                         user_name=body.chatName,
                         group_id=gid,
                         text=f'/{type_name} {body.chatText}',
                         state=103,
                         group_name='')
    return {'msgObj': msg, 'isGroup': is_group}


app = FastAPI()


# HelloWorld
@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-HTTPAPI'}


@app.post('/{command}')
async def universal_handler(command=None, body: ReqBody = None):
    if command is None:
        command = ['chat', 'write', 'voice', 'forgetme', 'remind']
    not_valid = pre_signature_check(body)
    if not_valid:  # 预检查错误信息
        return not_valid
    msg = receive_message(body, command)
    resp: PublicReturn
    finalMsg: str

    if msg['isGroup']:
        resp = await AppEvent.Group(Message=msg['msgObj'], bot_profile=ProfileManager.access_api(init=False),
                                    config=api_cfg)
    else:
        resp = await AppEvent.Friends(Message=msg['msgObj'], bot_profile=ProfileManager.access_api(init=False),
                                      config=api_cfg)

    final = resp.reply if resp.reply else resp.msg
    if not resp.status:  # 不成功
        return {'success': False, 'response': 'GENERAL_FAILURE'}
    if resp.voice and body.returnVoice:  # 语音正常、请求语音返回
        import base64
        http_res = Response(content=resp.voice, media_type='audio/ogg')
        http_res.headers['X-Bot-Reply'] = str(base64.b64encode(resp.reply.encode('utf-8')), 'utf-8')
        return http_res
    return {'success': True, 'response': final}


# Administration
@app.post('/admin/{action}')
async def admin(body: ReqBody, action: str):
    try:
        not_valid = pre_signature_check(body)
        if not_valid:
            return not_valid
        if body.chatId not in api_cfg.master:
            return {'success': False, 'response': 'OPERATION_NOT_PERMITTED'}
        admin_actions = ['set_user_cold', 'set_group_cold', 'set_token_limit', 'set_input_limit', 'see_api_key',
                         'del_api_key', 'add_api_key', 'set_per_user_limit', 'set_per_hour_limit', 'promote_user_limit',
                         'reset_user_usage', 'add_block_group', 'del_block_group', 'add_block_user', 'del_block_user',
                         'add_white_group', 'add_white_user', 'del_white_group', 'del_white_user', 'update_detect',
                         'open_user_white_mode', 'open_group_white_mode', 'close_user_white_mode',
                         'close_group_white_mode', 'open', 'close', 'change_head', 'change_style', 'auto_adjust']
        if action not in admin_actions:
            return {'success': False, 'response': 'INVAILD_ADMIN_ACTION'}
        msg = receive_message(body, action)
        resp = await AppEvent.MasterCommand(user_id=body.chatId, Message=msg['msgObj'], config=api_cfg)
        if not resp:
            return {'success': False, 'response': 'GENERAL_FAILURE'}
        return {'success': True, 'response': resp[0]}
    except Exception as e:
        logger.error(e)


# Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn

    ProfileManager.access_api(bot_name=api_cfg.botname[:6], bot_id=api_cfg.botid, init=True)
    uvicorn.run('APIServer:app', host=api_cfg['uvicorn_host'], port=api_cfg['uvicorn_port'],
                reload=False, log_level=api_cfg['uvicorn_loglevel'],
                workers=api_cfg['uvicorn_workers'])
