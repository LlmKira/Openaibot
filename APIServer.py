from utils import Setting
from fastapi import FastAPI
from fastapi.responses import Response
from API.Signature import APISignature
from pydantic import BaseModel
from utils.Base import ReadConfig
from utils.Data import create_message, PublicReturn
from loguru import logger
import App.Event as appe
import time, os


class ReqBody(BaseModel):
    chatText: str = ''
    chatId: int
    chatName: str
    groupId: int = -1
    timestamp: int = -1
    signature: str = ''
    returnVoice: bool = False
    chatName: str = ""


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
                            state=103,
                            group_name='')
    return {'msgObj': msgObj, 'isGroup': isGroup}


app = FastAPI()


# HelloWorld
@app.get('/')
def read_root():
    return {'HelloWorld': 'OpenAIBot-HTTPAPI'}


@app.post('/{command}')
async def universalHandler(command: str=['chat', 'write', 'voice', 'forgetme', 'remind'], body: ReqBody=None):
    notvalid = preCheck(body)
    if notvalid:  # 预检查错误信息
        return notvalid
    msg = newMsg(body, command)
    resp: PublicReturn
    finalMsg: str
    
    if msg['isGroup']:
        resp = await appe.Group(msg['msgObj'], apicfg)
    else:
        resp = await appe.Friends(msg['msgObj'], apicfg)
    
    finalMsg = resp.reply if resp.reply else resp.msg
    if not resp.status:  # 不成功
        return {'success': False, 'response': 'GENERAL_FAILURE', 'text': finalMsg}
    if resp.voice and body.returnVoice:  # 语音正常、请求语音返回
        import base64
        httpRes = Response(content=resp.voice, media_type='audio/ogg')
        httpRes.headers['X-Bot-Reply'] = str(base64.b64encode(resp.reply.encode('utf-8')),'utf-8')
        return httpRes
    return {'success': True, 'response': finalMsg}
    
    
#### Administration
@app.post('/admin/{action}')
async def admin(body: ReqBody, action: str):
    try:
        notvalid = preCheck(body)
        if notvalid:
            return notvalid
        if not body.chatId in apicfg.master:
            return {'success': False, 'response': 'OPERATION_NOT_PERMITTED'}
        admin_actions = ['set_user_cold', 'set_group_cold', 'set_token_limit', 'set_input_limit', 'see_api_key',
                         'del_api_key', 'add_api_key', 'set_per_user_limit', 'set_per_hour_limit', 'promote_user_limit',
                         'reset_user_usage', 'add_block_group', 'del_block_group', 'add_block_user', 'del_block_user',
                         'add_white_group', 'add_white_user', 'del_white_group', 'del_white_user', 'update_detect',
                         'open_user_white_mode', 'open_group_white_mode', 'close_user_white_mode',
                         'close_group_white_mode', 'open', 'close', 'disable_change_head', 'enable_change_head']
        if not action in admin_actions:
            return {'success': False, 'response': 'INVAILD_ADMIN_ACTION'}
        msg = newMsg(body, action)
        resp = await appe.MasterCommand(user_id=body.chatId, Message=msg['msgObj'], pLock=None, config=apicfg)
        if resp == []:
            return {'success': False, 'response': 'GENERAL_FAILURE', 'text': 'see console'}
        return {'success': True, 'response': resp[0]}
    except Exception as e:
        logger.error(e)


#### Run HTTP Server when executed by Python CLI
if __name__ == '__main__':
    import uvicorn
    
    Setting.api_profile_init(apicfg)
    uvicorn.run('APIServer:app', host=apicfg['uvicorn_host'], port=apicfg['uvicorn_port'],
                reload=apicfg['uvicorn_reload'], log_level=apicfg['uvicorn_loglevel'],
                workers=apicfg['uvicorn_workers'])
