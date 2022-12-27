![cover](https://raw.githubusercontent.com/sudoskys/Openaibot/main/docs/covers.png)

------------------------------------
<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-Other-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.7|8|9|10-green" alt="PYTHON" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Become-sponsor-DB94A2" alt="SPONSOR"></a>
</p>

<h2 align="center">Openaibot</h2>

OpenAI Chat Bot For Telegram. 在 Telegram 上使用 OpenAi 交互。

> Translate by deepl (wink~

This project uses `Api` authentication `Token` + context pooling to implement chat, and is not a reverse of `chatGPT`,
the **Python implementation** of the chatGPT-like is self-implemented by this bot.

The **Python implementation** of chatGPT **functionality** is implemented by this bot. but the Api costs money

**use Unofficial(self) async Api library to Speed up**

## Features

* chat (chat) chatGpt replica + NLP enhancements
* write independent speculation, continuation
* Set a constant story set point
* Multi maneger
* Multi Api key load, overrun popup.
* chatGPT api version implementation, not reverse preview's api
* Support for private chats
* Support for group chat
* Rate limiting support
* Support for usage management
* Whitelisting support
* Blacklisting support
* Support for content filtering
* (20221205) Api library changed to an Async library implemented in this repository
* Dynamic context trimming to prevent overruns
* Pre enhance support, Prompt Injection+ Web

See https://github.com/sudoskys/Openaibot/issues/1

**chatGpt**

🔭 Using `/chat + sentence` you can start a loop and then **just reply** to talk. Private chat messages or group
messages within 48 hours are automatically inferred and cropped using context, and the conversation can continue by
replying directly.

Use `/forgetme` resetAi's memory.

**Continued**

🥖 Use `/write` to continue writing without contextual speculation.

**Head**

Supports scenario setting, using `/remind` to design your own request headers. For
example `Ai plays an astronaut on a space station`.

**Description of these settings**

sent to the Api is

```markdown
head (left out defaults to The following dialogue is between the person and the Ai helper)
The key dialogue after nlp processing
The three original messages above that are retained
Start header (AI:)
```

## Initialization

* Pull/update the program

The install script will automatically backup the restore configuration, run it in the root directory (not in the program
directory)
If it is a minor update you can just ``git pull``.

```shell
curl -LO https://raw.githubusercontent.com/sudoskys/Openaibot/main/setup.sh && sh setup.sh
```

``cd Openaibot``

* [Docker](https://hub.docker.com/r/sudoskys/openaibot)

Docker images will release updates only after they are guaranteed to be stable.

```bash
git clone https://github.com/sudoskys/Openaibot
cd Openaibot
vim Config/service.json # see **Configure**
docker compose up -d

```

## Configure

### Configuring Redis

**local**

```shell
apt-get install redis
```

**Docker**

Configure `service.json`, the template example is below, you need to change host `localhost` to `redis`

### Configure dependencies

```bash
pip install -r requirements.txt
```

``pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple``

### Filters

Data/Danger.form One line of one blacklisted vocabulary. There must be at least one.

If not, the program will automatically pull down the cloud default list, and subsequent updetects will pull the cloud to
overwrite the local one.

You can turn this filter off by placing a one-line list, but I don't favour you doing this.

### Config/app.toml

`cp app_exp.toml app.toml`

`vim app.toml`
`nano app.toml`

**Configuration files**

```toml
[bot]
master = [555555, 66666] # master user id &account id
botToken = 'key'
INTRO = "POWER BY OPENAI" # suffix
ABOUT = "Created by github.com/sudoskys/Openaibot"
WHITE = "Group NOT in WHITE list"
Enhance_Server = { "https://www.expserver.com?q={}" = "auto", "http:/exp?q={}" = "auto" }
# 联网支持，自己找 server,{}将被替换为搜索词,目前联网回答的标识键为 Auto

# for bot , not openai
[proxy]
status = false
url = "http://127.0.0.1:7890"
```

[get Telegram botToken](https://t.me/BotFather)

### configure key

Configure key in bot private chat

```markdown
see_api_key - Several Api keys now
del_api_key - Delete Api key
add_api_key - add Api key
```

[OPENAI_API_KEY Application](https://beta.openai.com/account/api-keys), supports multi-key distribution load.
[Pricing Reference](https://openai.com/api/pricing/).

Please do not expose your `app.toml` to anyone

### Configure `service.json`

under `Config/service.json`. If there is no such file, the default value will be used. Deep coverage if available. Keys
that are not in the preset will not be completed.

```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": null
  },
  "plugin": {
    "search": [
      "https://www.exp.com/search?word={}"
    ],
    "time": "",
    "week": ""
  },
  "tts": {
    "status": false,
    "type": "vits",
    "vits": {
      "api": "http://127.0.0.1:9557/tts/generate",
      "limit": 70,
      "model_name": "some.pth",
      "speaker_id": 0
    },
    "azure": {
      "key": [
        "123"
      ],
      "limit": 70,
      "speaker": {
        "ZH": "zh-CN-XiaoxiaoNeural"
      },
      "location": "japanwest"
    }
  }
}
```

#### Middleware web server list

Provides external link support for plugins in ``openai_async/Chat/module/plugin``.

```json
{
  "plugin": {
    "search": [
      "https://www.exp.com/search?word={}"
    ]
  }
}
```

`search` is a search plugin that comes with us, the engines are all to be filled in by yourselves.

#### Redis

```json
{
  "host": "localhost",
  "port": 6379,
  "db": 0,
  "password": null
}
```

#### TTS

```shell
apt-get install ffmpeg
```

- status switch
- type Type

The Azure/Vits language type codes are all two-case abbreviated letters.

**Azure support notes**

[specific notes](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/)

- azure:limit Text within length will be converted
- azure:speaker
  speaker, [list of all sound engines](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=stt-tts)
- auzre:location Server resource address
- auzre:key api key

**VITS voice support instructions**

Api backend please use my packaged and modified MoeGoe https://github.com/sudoskys/MoeGoe running natively

- vits:limit Text within length will be converted
- vits:model_name model name, some.pth, in the model folder
- vits:speaker_id The ID of the speaker, see the model config

Install the dependencies and run the `server.py` file to use them by default.
To download the model, please find it yourself and note the appropriate protocol for the model. If it doesn't work, the
text may be longer than the set limit(`len()`).

## Run

* Run

```shell
nohup python3 main.py > /dev/null 2>&1 & 
```

* View the process

```shell
ps -aux|grep python3
```

* Terminate a process
  followed by the process number

```shell
kill -9  
```

## command

Restricted class setting set to ``1`` means no effect.

| command                                   | function                    | extra                                                                                                                                       |
|-------------------------------------------|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `/set_user_cold`                          | set user cooldown time      | can not send within the time 1 is unlimited                                                                                                 |
| `/set_group_cold`                         | Set group cooling time      | Cannot send within the time 1 is unlimited                                                                                                  |
| `/set_token_limit`                        | Set the output limit length | Api's 4095 limit is input + output, if it exceeds the limit, please reduce the output                                                       |
| `/set_input_limit`                        | Set input limit length      |                                                                                                                                             |
| `/config`                                 | get/backup config.json file | send file                                                                                                                                   |
| `/add_block_group` +id absolute value     | Prohibited                  | Effective directly Can be followed by multiple parameters, separated by spaces                                                              |
| `/del_block_group` + absolute value of id | Unban                       | Effective directly Can be separated with multiple parameters and spaces                                                                     |
| `/add_block_user` +Absolute value of id   | Forbidden                   | Effective directly Can be followed by multiple parameters, separated by spaces                                                              |
| `/del_block_user` + absolute value of id  | Unban                       | Effective directly Can be separated with multiple parameters and spaces                                                                     |
| `/add_white_group` +id absolute value     | Add                         | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/add_white_user` + id absolute value     | Add                         | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/del_white_group` +id absolute value     | Delisting                   | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/del_white_user` + absolute value of id  | Delisting                   | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/update_detect`                          | Update sensitive words      |                                                                                                                                             |
| `/open_user_white_mode`                   | Open user whitelist         |                                                                                                                                             |
| `/open_group_white_mode`                  | Open group whitelist        |                                                                                                                                             |
| `/close_user_white_mode`                  | close user whitelist        |                                                                                                                                             |
| `/close_group_white_mode`                 | close group whitelist       |                                                                                                                                             |
| `/open`                                   | Open the robot              |                                                                                                                                             |
| `/close`                                  | close the robot             |                                                                                                                                             |
| `/chat`                                   | Conversation                | Each time /chat starts over, forgetting the record. Replies cannot be indexed after 24 hours in the group, and private chats are permanent. |
| `/write`                                  | continue writing            | continue writing.                                                                                                                           |
| `/see_api_key`                            | Several Api keys now        |                                                                                                                                             |
| `/remind`                                 | Persona                     | Fixed reminder.                                                                                                                             |
| `/del_api_key` +key                       | Delete Api key              | Can follow multiple parameters, separated by spaces                                                                                         |
| `/add_api_key` +key                       | Add Api key                 | Can follow multiple parameters, separated by spaces                                                                                         |
| `/set_per_user_limit`                     | total user allocation limit | 1 is unlimited per user                                                                                                                     |
| `/set_per_hour_limit`                     | user hour usage             | 1 is unlimited, per user                                                                                                                    |
| `/reset_user_usage`+userID                | Reset user quota            | Measured by user Can be followed by multiple parameters, separated by spaces                                                                |
| `/promote_user_limit`+userID+limit        | Promote the user's limit    | Measured by user 1 is the default, can be followed by multiple parameters, separated by spaces                                              |
| `/disable_change_head`                    | disalbe head setting        | Setting again will reset to empty                                                                                                           |
| `/enable_change_head`                     | enable head setting         |                                                                                                                                             |
| `/remind`                                 | how ai perform self         | Fixed cue words                                                                                                                             |
| `/forgetme`                               | 忘记我                         |                                                                                                                                             |
| `/voice`                                  | VITS/AZURE  TTS             |                                                                                                                                             |

### Sample table

```markdown
chat - Talking
write - complement
remind - persona
forgetme - reset
voice - 语音支持
set_user_cold - set user cooldown
set_group_cold - sets the group cooldown time
set_token_limit - set output limit length
set_input_limit - sets the input limit length
see_api_key - now several Api keys
del_api_key - remove Api key
add_api_key - add Api key
config - get/backup hotfile
set_per_user_limit - set the normal user limit
set_per_hour_limit - set the hourly user limit
promote_user_limit - raise user limit
reset_user_usage - reset user limits
add_block_group - disable a group
del_block_group - unblock a group
add_block_user - disable a user
del_block_user - unblock a user
add_white_group - add a whitelisted group
add_white_user - add whitelisted users
del_white_group - delist a whitelisted group
del_white_user - delist a whitelisted person
update_detect - update sensitive words
open_user_white_mode - open user whitelist
open_group_white_mode - open group whitelist
close_user_white_mode - turn off user whitelisting
close_group_white_mode - Turn off group whitelisting
open - turn on bots
close - disables the bot
disable_change_head - allow setting of head
enable_change_head - disable_change_head
help - help
```

## API

Please see https://github.com/sudoskys/Openaibot/blob/main/API.md for open API documentation.
The API server and Telegram Bot service are not at the same pace of development, usually Telegram
The API server adapts after a new commit has been made to the Bot. The API server may not function properly when certain
import modules are changed. In this case, you can switch to the apiserver branch to get a stable version of the API
server.

## Middleware development

There is a middleware between the memory pool and the analytics that provides some networked retrieval support and
operational support. It can be spiked with services that interface to other Api's.

**Table**

| plugins  | desc       | server                                 |
|----------|------------|----------------------------------------|
| `time`   | now time   | `""`,no need                           |
| `week`   | week time  | `""`,no need                           |
| `search` | web search | `["some.com?searchword={}"]`,must need |

**Prompt Injection**

Use `""` `[]` to emphasise content. Triggers have requirements for formal question
interrogatives, `introductions`, `query` requests, less than 80 characters, etc.
Triggering is implicit, short formal interrogatives will trigger.

### Development tips

First create a file in `openai_async/Chat/module/plugin` without underscores (`_`) in the file name.

**Template**

```python
from ..platform import ChatPlugin, PluginConfig
from ._plugin_tool import PromptTool
import os

modulename = os.path.basename(__file__).strip(".py")


@ChatPlugin.plugin_register(modulename)
class Week(object):
    def __init__(self):
        self._server = None
        self._text = None
        self._time = ["time", "多少天", "几天", "时间", "几点", "今天", "昨天", "明天", "几月", "几月", "几号",
                      "几个月",
                      "天前"]

    def check(self, params: PluginConfig) -> bool:
        if PromptTool.isStrIn(prompt=params.text, keywords=self._time):
            return True
        return False

    def process(self, params: PluginConfig) -> list:
        _return = []
        self._text = params.text
        # 校验
        if not all([self._text]):
            return []
        # GET
        from datetime import datetime, timedelta, timezone
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        now = bj_dt.strftime("%Y-%m-%d %H:%M")
        _return.append(f"Current Time UTC8 {now}")
        return _return
```

`openai_async/Chat/module/plugin/_plugin_tool.py` provides some tool classes, PR is welcome

## Other

### Statistics `analysis.json`

If you don't have one, please populate it with `{}`

This file is a frequency statistic, the number of requests made in 60s.

As users use it, `total usage` will be updated to this file. If you want to back up usage data, please back up the Redis
database.

### Configuration file `Config.json`

needs to be backed up frequently using the command. If not please create a new populated `{}` or delete it and it will
automatically merge the missing keys for repair.

### Default parameters

- Group revert memory to 48 hours
- Usage limit is 15000/h
- Memory capacity of 80 dialogue pairs

### prompt_server.py

Peripheral Prompt trimming interface to give support to other projects.

### Declarations

```markdown
1. This project is not an official Openai project.
2. is not responsible for any content generated by the bot.
3. 部分套件可能无法商业使用，请自担风险。
```

### QuickDev

Quick Dev by MVC framework https://github.com/TelechaBot/BaseBot

### API

You can view the API documentation at https://github.com/sudoskys/Openaibot/blob/main/API.md .
Since the development progress differs between the API server and Telegram Bot, the API server may not work properly
when there are unadapted changes on some imported modules. In that case, you can use the apiserver branch to get a
stable API server.

### Last performance analysis

**Daily load 300MB**

### Thanks to

- Contributors
- [Text Analysis Tool Library](https://github.com/murray-z/text_analysis_tools)
- [MoeGoe Voice](https://github.com/CjangCjengh/MoeGoe)

## FOSSA

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)
