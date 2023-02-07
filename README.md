![cover](https://raw.githubusercontent.com/LLMKira/Docs/main/docs/cover.png)
------------------------------------
<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-AGPL-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.8|9|10|11-green" alt="Python" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Buyme-milk-DB94A2" alt="SPONSOR"></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small"/></a>
</p>

<h2 align="center">OpenaiBot</h2>

全平台，多模态(语音/图片)理解，自维护套件，实时信息支持

If you don't have the instant messaging platform you need or you want to develop a new application, you are welcome to
contribute to this repository.
You can develop a new Controller by using `Event.py`.

We use the self-maintained llm framework [llm-kira](https://github.com/LLMKira/llm-kira) to implement the conversation
client.

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

For Arm architecture servers: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

### 📦 Deploy/Renew

```shell
curl -LO https://raw.githubusercontent.com/LLMKira/Openaibot/main/setup.sh && sh setup.sh
```

### 🍽 Configure

- init

```shell
cp Config/app_exp.toml Config/app.toml

nano Config/app.toml
```

- Data

```shell
apt-get install redis
systemctl start redis.service
```

- Config/app.toml

```toml
# Comment out which part you don't want to start

# QQ Bot
[Controller.QQ]
master = [114, 514] # master user id
account = 0
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
master = [114, 514] # master user id
botToken = '' # Bot Token @botfather
trigger = false
INTRO = "POWER BY OPENAI"
ABOUT = "Created by github.com/LLMKira/Openaibot"
WHITE = "Group NOT in WHITE list"

# 设置的代理，但是不代理 openai api, 只代理 bot
proxy = { status = false, url = "http://127.0.0.1:7890" }

# 基础对话事件服务器，Web支持或者音箱用
[Controller.BaseServer]
host = "127.0.0.1"
port = 9559
```

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
pm2 start pm.json
```

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

### 🧀 More Docs

Details On [Deploy Guide](https://llmkira.github.io/Docs/en/guide/getting-started)

Network Plugins/Proxy Settings/Custom Model Names/Speech Services/Picture Understanding/Censor Configuration
Please see [Service Configuration Guide](https://llmkira.github.io/Docs/guide/service)

详细接口/服务配置/自定义 请查看文档 [Deploy Guide](https://llmkira.github.io/Docs/guide/getting-started)

插件设置/代理设置/自定义模型名称/语音服务/图片理解/审查配置
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

## 📃 License

```
This project open source and available under
the [AGPL License](https://github.com/LLMKira/Openaibot/blob/main/LICENSE).
```

[CLAUSE](https://github.com/LlmKira/Openaibot/blob/main/CLAUSE.md) 说明了如何授权，声明，附加条款等内容。

### Fossa

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)

> You wouldn't believe it, but Ai also wrote part of this Readme