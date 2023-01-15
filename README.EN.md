![cover](https://raw.githubusercontent.com/sudoskys/Openaibot/main/docs/cover.png)

------------------------------------
<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-Other-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.7|8|9|10-green" alt="PYTHON" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Become-sponsor-DB94A2" alt="SPONSOR"></a>
</p>

<h2 align="center">Openaibot</h2>
> Translate by deepl (wink~

OpenAI Chat Bot For IM. Use OpenAi Interaction on IM.

**If your instant messaging platform is not available or you want to develop a new app, we welcome your contribution to
this repository. You can develop a new Controller by dispatching generic event layer.**

This project uses GPT API + context memory pool to realize chat, not the reverse of chatGPT, and the Python
implementation of chatGPT-like is self-implemented.

Using GPT3 + injection to get close to ChatGpt, using an extensible framework, when ChatGPT is commercialized, it will
switch into new Api immediately.

* Close to chatGPT, currently chatGPT has not opened interfaces and basically all replaced with Dafanqi.
* Dependent libraries are switched from official synchronous to self-maintained asynchronous libraries.
* Reverse has no way out, our advantage is at the forefront of trying and providing mature interactive experience.
* This repository welcomes all contributors.

## Features

* Independent inference, continuation writing
* Memory bucket mechanism, weight correlation allocation, more intelligent context
* Support API
* Style Chat!
* Support private chat
* Support group chat
* Multi-host management
* Support rate limiting
* Content filtering support
* Usage management support
* Setting fixed host settings
* White list system support
* Blacklist system support
* Multi-platform, strong generality
* Comprehensive content security functions
* Universal interface supported by multiple platforms
* Support active reply (For Fun)
* Dynamic context clipping to prevent overuse
* Multiple Api key loads for convenient management and overuse pop-up
* Pluginization for real-time content support, Prompt Injection for better Chat experience
* Replace chatGpt with your own written chatGpt Openai api Python implementation
* Official dependency library does not support asynchronous, a large number of requests will block, replace with your
  own written asynchronous library (recently official supports asynchronous)

🔭 Using `/chat + sentence` you can start a loop and then **just reply** to talk. Private chat messages or group
messages within 48 hours are automatically inferred and cropped using context, and the conversation can continue by
replying directly.

Use `/forgetme` resetAi's memory.

**Continued**

🥖 Use `/write` to continue writing without contextual speculation.

**Head**

Supports scenario setting, using `/remind` to design your own request headers. For
example `Ai plays an astronaut on a space station`.

**Style**

Support scene setting, use `/style` to design your own style, Ai
Will tend to use the vocabulary in the corpus, the grammar
is `(enhance),((enhance pro)),[[weak]],{enhance}, (Chinese commas are also acceptable)`

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
systemctl start redis.service
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
# 不想启动就注释掉那一部分

# QQ
[Controller.QQ]
master = [114, 514] # master user id , 账号 ID
account = 0
http_host = 'http://localhost:8080'   # Mirai http服务器
ws_host = 'http://localhost:8080'   # Mirai Websocket服务器
verify_key = ""
trigger = false # 合适的时候主动回复
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot" # 关于命令返回
WHITE = "Group NOT in WHITE list" # 黑白名单提示

# Telegram
[Controller.Telegram]
master = [114, 514] # master user id , 账号 ID
botToken = '' # 机器人密钥
trigger = false # 合适的时候主动回复
INTRO = "POWER BY OPENAI"  # 后缀
ABOUT = "Created by github.com/sudoskys/Openaibot" # 关于命令返回
WHITE = "Group NOT in WHITE list" # 黑白名单提示

[Controller.BaseServer]
port = 9559
# 提供基础Api接口供Web使用
```

### Configure Telegram Bot

#### BotToken

[Telegram botToken](https://t.me/BotFather)

Then turn off privacy mode or raise the bot to administrator before it can be used.

### Configuring QQ bot

[Configure bot backend](https://graiax.cn/before/install_mirai.html)

### Set Openai Api Key

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
  "proxy": {
    "status": false,
    "url": "localhost:7890"
  },
  "plugin": {
    "details": "",
    "time": "",
    "week": ""
  },
  "moderation_type": [
    "self-harm",
    "hate",
    "sexual",
    "hate/threatening",
    "sexual/minors",
    "violence",
    "violence/graphic"
  ],
  "tts": {
    "status": true,
    "type": "none",
    "vits": {
      "api": "http://127.0.0.1:9557/tts/generate",
      "limit": 70,
      "model_name": "some.pth",
      "speaker_id": 0
    },
    "azure": {
      "key": [
        ""
      ],
      "limit": 70,
      "speaker": {
        "chinese": "zh-CN-XiaoxiaoNeural"
      },
      "location": "japanwest"
    }
  }
}
```

#### Middleware web server list

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

Plugins that are placed in the `plugin` field will only be enabled.

| plugins   | desc              | value/server                                          | use                                   |
|-----------|-------------------|-------------------------------------------------------|---------------------------------------|
| `time`    | now time          | `""`,no need                                          | `明昨今天`....                            |
| `week`    | week time         | `""`,no need                                          | `周几` .....                            |
| `search`  | Web Search        | `["some.com?searchword={}"]`,must need                | `查询` `你知道` len<80 / end with`?`len<15 |
| `duckgo`  | Web Search        | `""`,no need,but need `pip install duckduckgo_search` | `查询` `你知道` len<80 / end with`?`len<15 |
| `details` | answer with steps | `""`,no need                                          | Ask for help `how to`                 |

[Plugin Table](https://github.com/sudoskys/openai-kira#plugin)

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

| command                                   | function                           | extra                                                                                                                                       |
|-------------------------------------------|------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `/set_user_cold`                          | set user cooldown time             | can not send within the time 1 is unlimited                                                                                                 |
| `/set_group_cold`                         | Set group cooling time             | Cannot send within the time 1 is unlimited                                                                                                  |
| `/set_token_limit`                        | Set the output limit length        | Api's 4095 limit is input + output, if it exceeds the limit, please reduce the output                                                       |
| `/set_input_limit`                        | Set input limit length             |                                                                                                                                             |
| `/config`                                 | get/backup config.json file        | send file                                                                                                                                   |
| `/add_block_group` +id absolute value     | Prohibited                         | Effective directly Can be followed by multiple parameters, separated by spaces                                                              |
| `/del_block_group` + absolute value of id | Unban                              | Effective directly Can be separated with multiple parameters and spaces                                                                     |
| `/add_block_user` +Absolute value of id   | Forbidden                          | Effective directly Can be followed by multiple parameters, separated by spaces                                                              |
| `/del_block_user` + absolute value of id  | Unban                              | Effective directly Can be separated with multiple parameters and spaces                                                                     |
| `/add_white_group` +id absolute value     | Add                                | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/add_white_user` + id absolute value     | Add                                | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/del_white_group` +id absolute value     | Delisting                          | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/del_white_user` + absolute value of id  | Delisting                          | Need to enable the whitelist mode to take effect Can be separated with multiple parameters and spaces                                       |
| `/update_detect`                          | Update sensitive words             |                                                                                                                                             |
| `/open_user_white_mode`                   | Open user whitelist                |                                                                                                                                             |
| `/open_group_white_mode`                  | Open group whitelist               |                                                                                                                                             |
| `/close_user_white_mode`                  | close user whitelist               |                                                                                                                                             |
| `/close_group_white_mode`                 | close group whitelist              |                                                                                                                                             |
| `/open`                                   | Open the robot                     |                                                                                                                                             |
| `/close`                                  | close the robot                    |                                                                                                                                             |
| `/chat`                                   | Conversation                       | Each time /chat starts over, forgetting the record. Replies cannot be indexed after 24 hours in the group, and private chats are permanent. |
| `/write`                                  | continue writing                   | continue writing.                                                                                                                           |
| `/see_api_key`                            | Several Api keys now               |                                                                                                                                             |
| `/remind`                                 | Persona                            | Fixed reminder.                                                                                                                             |
| `/del_api_key` +key                       | Delete Api key                     | Can follow multiple parameters, separated by spaces                                                                                         |
| `/add_api_key` +key                       | Add Api key                        | Can follow multiple parameters, separated by spaces                                                                                         |
| `/set_per_user_limit`                     | total user allocation limit        | 1 is unlimited per user                                                                                                                     |
| `/set_per_hour_limit`                     | user hour usage                    | 1 is unlimited, per user                                                                                                                    |
| `/reset_user_usage`+userID                | Reset user quota                   | Measured by user Can be followed by multiple parameters, separated by spaces                                                                |
| `/promote_user_limit`+userID+limit        | Promote the user's limit           | Measured by user 1 is the default, can be followed by multiple parameters, separated by spaces                                              |
| `/change_style`                           | setting prefer words               | Setting it again will reset to empty                                                                                                        |
| `/change_head`                            | setting header                     | Setting it again will reset to empty                                                                                                        |
| `/forgetme`                               | forget me                          |                                                                                                                                             |
| `/voice`                                  | VITS/AZURE TTS                     |                                                                                                                                             |
| `/trigger`                                | Active reply mode                  | Global settings or/only members of the management group can start this group mode                                                           |
| `/style`                                  | style specification                | global setting or /user setting                                                                                                             |
| `/auto_adjust`                            | Automatically optimize performance | owner                                                                                                                                       |

### Sample table

```markdown
chat - talk
write - continue writing
forgetme - reset memory
reminder - Scene setting cancel overwrite with short text
voice - voice support
trigger - Admin initiates unsolicited responses
style - set the preferred word
auto_adjust - automatic optimizer
set_user_cold - set user cooldown
set_group_cold - set group cooldown
set_token_limit - set output limit length
set_input_limit - set input limit length
see_api_key - Several Api keys now
del_api_key - Delete Api key
add_api_key - add Api key
config - get/backup hot configuration file
set_per_user_limit - set normal user limit
set_per_hour_limit - set user hour limit
promote_user_limit - Promote user limit
reset_user_usage - Reset user usage
add_block_group - block group
del_block_group - Unblock group
add_block_user - block user
del_block_user - Unblock user
add_white_group - add whitelist group
add_white_user - add whitelist user
del_white_group - delist whitelist group
del_white_user - remove whitelist user
update_detect - update sensitive words
open_user_white_mode - open user whitelist
open_group_white_mode - open group whitelist
close_user_white_mode - close user whitelist
close_group_white_mode - close group whitelist
open - open the robot
close - close the robot
change_head - set head switch
change_style - set the style switch
help - help
```

## API

Please see https://github.com/sudoskys/Openaibot/blob/main/docs/API.md for open API documentation.
The API server and Telegram Bot service are not at the same pace of development, usually Telegram
The API server adapts after a new commit has been made to the Bot. The API server may not function properly when certain
import modules are changed. In this case, you can switch to the apiserver branch to get a stable version of the API
server.

## Middleware development

There is a middleware between the memory pool and the analytics that provides some networked retrieval support and
operational support. It can be spiked with services that interface to other Api's.

https://github.com/sudoskys/openai-kira#plugin-dev

## Other

### Muti Controller

| Controller | suffix_id | desc |
|------------|-----------|------|
| QQ         | 101       |      |
| Telegram   | 100       |      |
| Api        | 103       |      |

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

## CLAUSE

CLAUSE 说明了如何授权，声明，附加条款等内容。

![CLAUSE](https://github.com/sudoskys/Openaibot/main/CLAUSE.md)