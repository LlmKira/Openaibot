![cover](https://raw.githubusercontent.com/LLMKira/Docs/main/docs/cover.png)
------------------------------------
<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-AGPL-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.8|9|10|11-green" alt="Python" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Buyme-milk-DB94A2" alt="SPONSOR"></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small"/></a>
</p>

<h2 align="center">OpenaiBot</h2>

[中文](https://github.com/LlmKira/Openaibot/blob/main/README_ZH.md)

全平台，多模态(语音/图片)理解，自维护套件，实时信息支持

If you don't have the instant messaging platform you need or you want to develop a new application, you are welcome to
contribute to this repository.
You can develop a new Controller by using `Event.py`.

We use the self-maintained llm framework [llm-kira](https://github.com/LLMKira/llm-kira) to implement the conversation
client.

**Please submit an issue/discussion if you have a deployment issue rather than emailing me**

## 🥽 Feature

* Async
* Support for rate limiting
* Support for private chats, group chats
* Support for black and white list system
* Support for usage management, persona, custom words style 🤖
* Memory pool guarantees 1000 rounds of contextual memory 💾
* Multi-platform, universal use, also supports local voice assistant 🗣️
* Multiple Api key polling pools for easy management and overflow pop-ups 📊
* Active search for content to reply to and support for Sticker replies 😊
* Universal interface for multi-platform support, theoretically allows access to any chat platform 🌐
* Content security removable components, also supports official Api content filtering 🔒
* Real-time web indexing support, universal crawler (supports UrlQueryHtml url?q={}) 🕸️
* Multimodal interaction support, image Blip comprehension support, voice recognition 👂 , sticker support 😎

## 🪜 Deploy It

### 🔨 Check

Make sure your server has 1GB of RAM and 10GB of free storage.

For Arm architecture servers: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` (The setup.sh can now
automatically install rust.)

### 📦 Deploy/Renew

```shell
curl -LO https://raw.githubusercontent.com/LLMKira/Openaibot/main/setup.sh && sh setup.sh
```

For Chinese users

```shell
curl -LO https://raw.kgithub.com/LLMKira/Openaibot/main/setup.sh && sh setup.sh
```

Or [Docker Deploy](https://llmkira.github.io/Docs/guide/getting-started#docker)

### 🍽 Configure

- set Redis

```shell
apt-get install redis
systemctl enable redis.service --now
```

- edit bot config

```shell
cp Config/app_exp.toml Config/app.toml

nano Config/app.toml
```

```toml
# Comment out which part you don't want to start
# 注释你不需要的部分

# QQ Bot
[Controller.QQ]
master = [114, 514] # QQ number
account = 0  # Bot s QQ number
http_host = 'http://localhost:8080'   # Mirai http Server
ws_host = 'http://localhost:8080'   # Mirai Websocket Server
verify_key = ""
trigger = false # Proactive response when appropriate
INTRO = "POWER BY OPENAI"  # Suffixes for replies
ABOUT = "Created by github.com/LLMKira/Openaibot" # /about
WHITE = "Group NOT in WHITE list" # Whitelist/Blacklist tips
# Proxy set, but does not proxy openai api, only bot
proxy = { status = false, url = "http://127.0.0.1:7890" }

# Telegram Bot
[Controller.Telegram]
master = [114, 514] # User Id @JsonDumpBot
botToken = '' # Bot Token @botfather
trigger = false
INTRO = "POWER BY OPENAI"
ABOUT = "Created by github.com/LLMKira/Openaibot"
WHITE = "Group NOT in WHITE list"
# 设置的代理，只代理 bot  openai api->service.json 
proxy = { status = false, url = "http://127.0.0.1:7890" }

# 基础对话事件服务器，Web支持或者音箱用&Use by Voice Assistant
[Controller.BaseServer]
host = "127.0.0.1"
port = 9559
```

If you want configure the backend or openai proxy. Please
Check [Deploy Docs](https://llmkira.github.io/Docs/guide/service)

### 🪶 App Token

- Telegram

[Telegram BotToken Request](https://t.me/BotFather)

Make sure *the bot is a group admin* or *privacy mode is turned off*.

- QQ

[Configuring the QQ bot](https://graiax.cn/before/install_mirai.html)

### 🌻 Run Bot

Our robots can be started in multiple processes.

```shell
apt install npm
npm install pm2@latest -g
# or
yarn global add pm2

# test bot
python3 main.py

# run bot
pm2 start pm2.json


pm2 status

# stop bot
pm2 stop pm2.json
pm2 stop xx(id)
pm2 restart x(id)
```

Once configured, send a message and use the `/add_white_user` command to add your platform ID returned by the bot to the
whitelist and you will be able to talk.
Or use `/close_group_white_mode` to turn off the bot's *group whitelist* mode.

### 🎤 Or Run Voice Assistant

In addition to the robot, we also have a voice assistant.

Voice Assistant is a web-dependent voice assistant that you can easily run on small devices through Azure or Openai's
recognition services.

- Run BaseEvent Server

```toml
# 基础对话事件服务器，Web支持或者音箱用
[Controller.BaseServer]
port = 9559
```

- Run Vits Server

https://github.com/LlmKira/MoeGoe

- Run Assistant

```shell
cd Assistant
cat install.md
pip3 install -r requirements.txt
python3 clinet.py
```

### 🥕 Add Api Key

Use `/add_api_key` Command add [OpenaiKey](https://beta.openai.com/account/api-keys) to `Config/api_keys.json`.

### 🫧 About ID

You'll be wondering about our multi-platform ID system. This is how we store your ID in our
json/database: `real_id` + `suffix`.

- toml

Use your real ID in `app.toml`, which is the whitelist prompt without the suffix.

- json/command

When using the user/group authorization command, you need to follow the real ID with the corresponding suffix ID.

| Controller | suffix_id | desc |
|------------|-----------|------|
| QQ         | 101       |      |
| Telegram   | 100       |      |
| Api        | 103       |      |

### 🥪 About Models

#### ChatGpt

| models             | token limit | cost                                                       |
|--------------------|-------------|------------------------------------------------------------|
| gpt-3.5-turbo      | 4095        | optimized for chat at 1/10th the cost of text-davinci-003. |
| gpt-3.5-turbo-0301 | 4095        | optimized for chat at 1/10th the cost of text-davinci-003. |

#### GPT3

| models           | token limit | cost                                                          |
|------------------|-------------|---------------------------------------------------------------|
| code-davinci-002 | 8000        | During this initial limited beta period, Codex usage is free. |
| code-cushman-001 | 2048        | During this initial limited beta period, Codex usage is free. |
| text-davinci-003 | 4000        | $0.0200  /1K tokens                                           |
| text-curie-001   | 2048        | $0.0020  /1K tokens                                           |
| text-babbage-001 | 2048        | $0.0005  /1K tokens                                           |
| text-ada-001     | 2048        | $0.0004  /1K tokens                                           |

### Keyword filtering configuration

To prevent malicious inducement and attacks, we have two measures: OpenAI TosApi filtering and simplified/traditional Chinese
keyword filtering.

- Simplified/traditional Chinese keyword filtering(Only For Chinese)

If not exist, the sensitive word file will be automatically initialized into `Data/Danger.form`, and it can be disabled
by clearing it to one line.

- OpenAI TosApi filtering

Leave the inspection type array empty to disable the filter.

Please see [Service Configuration Guide](https://llmkira.github.io/Docs/guide/service).

### 🌽 `/Config` File

Our `llm-kira` dependency library is stored in the current package directory when there is no Redis support.

The application itself is stored in Redis for robustness, except for `api_keys.json`, `service.json`
and `assistants.json`.

If you have `config.json`, the application will automatically initialise this file. And you can update the configuration
to this file using the `/config` command.

### 🎸 Command

Due to lack of maintainers, some commands only work on some platforms.

```shell
chat - talk
write - continue writing
forgetme - reset memory
remind - Scene setting cancel overwrite with short text
voice - voice support
style - set the preferred word

trigger - Admin initiates unsolicited responses
trace - Admin activates automatic tracking of associated channels
cross - whether the Admin starts a cross-response
silent - Admin starts silent error reporting

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

### 🧀 More Docs

Details On [Deploy Guide](https://llmkira.github.io/Docs/en/guide/getting-started)

Network Plugins/Proxy Settings/Custom Model Names/Speech Services/Picture Understanding/Censor Configuration
Please see [Service Configuration Guide](https://llmkira.github.io/Docs/guide/service)

详细接口/服务配置/自定义 请查看文档 [Deploy Guide](https://llmkira.github.io/Docs/guide/getting-started)

贴纸设置/代理设置/切换其他模型/语音服务/图片理解/审查配置
请查看 [服务配置](https://llmkira.github.io/Docs/guide/service)

## 🤗 Join Our Community

<a href="https://github.com/LLMKira/Openaibot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=LLMKira/Openaibot" />
</a>

## ❤ Thanks

- [QuickDev](https://github.com/TelechaBot/BaseBot)
- [LLM Kira](https://github.com/LLMKira/llm-kira)
- [text_analysis_tools](https://github.com/murray-z/text_analysis_tools)
- [MoeGoe Voice](https://github.com/CjangCjengh/MoeGoe)
- [duckduckgo_search](https://github.com/deedy5) @deedy5

## 🍞 Other similar projects

- ChatGPT Mirai Bot is a QQ bot based on the ChatGPT Web Api& Edge Api & GPT3.5

https://github.com/lss233/chatgpt-mirai-qq-bot

## 📃 License

```markdown
This project open source and available under
the [AGPL License](https://github.com/LLMKira/Openaibot/blob/main/LICENSE).
```

[CLAUSE](https://github.com/LlmKira/Openaibot/blob/main/CLAUSE.md) 说明了如何授权，声明，附加条款等内容。

### Fossa

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)

> You wouldn't believe it, but Ai also wrote part of this Readme
