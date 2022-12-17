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
* Pre enhance support, Web Connection

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

## Configure

### Configuring Redis

**local**

```shell
apt-get install redis
```

**Docker + persistence (saved in . /redis directory)**

```
docker run --name redis -d -v $(pwd)/redis:/data -p 6379:6379 redis redis-server --save 60 1 --loglevel warning
```

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

**configure (one or more) key**

```markdown
see_api_key - now several Api keys
del_api_key - remove Api key
add_api_key - add Api key
```

[OPENAI_API_KEY application](https://beta.openai.com/account/api-keys)

[Pricing Reference](https://openai.com/api/pricing/)

Please don't expose your `app.toml` to anyone

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

### Sample table

```markdown
chat - Talking
write - complement
remind - persona
forgetme - reset
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

## Other

### Statistics

``analysis.json`` is the frequency statistic, the number of requests in 60s.

And total usage, which doesn't contain all the usage data, it's just pulled from redis

### Config.json

will automatically merge the missing keys to fix them.

### Default parameters

- Group revert memory to 48 hours
- Usage limit is 15000/h
- Memory capacity of 80 dialogue pairs

### Middleware support

There is a middleware between the memory pool and the analysis that can provide some networking retrieval support and
operational support. Services that can interface with other Api's can be spiked.

### prompt_server.py

Peripheral Prompt trimming interface to give support to other projects.

### Declarations

```markdown
1. This project is not an official Openai project.
2. is not responsible for any content generated by the bot.
```

### QuickDev

Quick Dev by MVC framework https://github.com/TelechaBot/BaseBot

### Last performance analysis

**Daily load 300MB**

### Thanks to

- Contributors
- [Text Analysis Tool Library](https://github.com/murray-z/text_analysis_tools)

## FOSSA

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)
