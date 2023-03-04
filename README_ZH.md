![cover](https://raw.githubusercontent.com/LLMKira/Docs/main/docs/cover.png)
------------------------------------
<p align="center">
  <img alt="License" src="https://img.shields.io/badge/LICENSE-AGPL-ff69b4">
  <img src="https://img.shields.io/badge/Python-3.8|9|10|11-green" alt="Python" >
  <a href="https://afdian.net/a/Suki1077"><img src="https://img.shields.io/badge/Buyme-milk-DB94A2" alt="SPONSOR"></a>
  <a href="https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small" alt="FOSSA Status"><img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small"/></a>
</p>

<h2 align="center">OpenaiBot</h2>

[ENGLISH](https://github.com/LlmKira/Openaibot/blob/main/README.md)

全平台，多模态(语音/图片)理解，自维护套件，实时信息支持

如果您没有所需的即时消息平台，或者您想开发一个新的应用程序，欢迎您为该仓库贡献。

您可以使用“Event.py”开发新的控制器。

我们使用自维护的 [llm-kira](https://github.com/LLMKira/llm-kira) 实现对话客户端

**有部署问题请提交 Issue /讨论 而不是给我发邮件或私聊.**

## 🥽 Feature

* 异步
* 支持聊天速率限制
* 支持私聊、群聊
* 支持黑名单和白名单系统
* 支持使用管理、角色以及自定义行文风格 🤖
* 内存池保证1000轮的上下文内存保存 💾
* 跨平台，还支持本地语音助手 🗣️
* 允许多个Api密钥轮询，便于管理，失效自动弹出 📊
* 主动搜索要回复的内容并支持贴纸回复 😊
* 跨平台支持的通用接口，理论上允许访问任何聊天平台 🌐
* 拥有可移除的内容安全组件，也支持官方Api过滤内容 🔒
* 实时网页索引支持，万能爬虫 (支持 UrlQueryHtml url?q={}) 🕸️
* 多模态交互支持，图像Blip理解支持，语音识别 👂 , 贴纸支持 😎

## 🪜 Deploy It

### 🔨 Check

请确保您的服务器有 1GB 的 RAM 和 10GB的 可用存储空间

对于 Arm 架构服务器: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

### 📦 Deploy/Renew

```shell
curl -LO https://raw.githubusercontent.com/LLMKira/Openaibot/main/setup.sh && sh setup.sh
```

连不上 Github 请使用下面的镜像

```shell
curl -LO https://raw.kgithub.com/LLMKira/Openaibot/main/setup.sh && sh setup.sh
```

或者使用 [Docker Deploy](https://llmkira.github.io/Docs/guide/getting-started#docker)

### 🍽 Configure

- 配置数据服务器

```shell
apt-get install redis
systemctl start redis.service
```

- 配置/app.toml

```shell
cp Config/app_exp.toml Config/app.toml

nano Config/app.toml
```

```toml
# Comment out which part you don't want to start

# QQ Bot
[Controller.QQ]
master = [114, 514] # 你的QQ号码
account = 0 # 机器人的 QQ 号码
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
master = [114, 514] # 你的用户 ID 找 @JsonDumpBot 看 message from id
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

如果你想要配置其他模型或者配置 OpenaiApi 的代理，请查看 [Deploy Docs](https://llmkira.github.io/Docs/guide/service)

### 🪶 App Token

- Telegram

[Telegram BotToken Request](https://t.me/BotFather)

在部署先请重新生成token防止其他服务占用轮询。

另外请确保 *机器人是组管理员* 或 *关闭隐私模式*.

- QQ

[Configuring the QQ bot](https://graiax.cn/before/install_mirai.html)

### 🌻 Run Bot

我们的机器人可以多进程运行

```shell
apt install npm
npm install pm2@latest -g
# or
yarn global add pm2

# test bot
python3 main.py

# run bot
pm2 start pm2.json

# 查看机器人的运行状况

pm2 status

# 停止
pm2 stop pm2.json

# 重启
pm2 restart 任务id

```

配置后，发一条消息，使用 `/add_white_user` 命令加入机器人返回的你的平台ID到白名单，就可以对话啦。
或者使用 `/close_group_white_mode` 关闭机器人的 *群组白名单* 模式。

### 🎤 Or Run Voice Assistant

除了机器人，我们还有语音助手.

Voice Assistant 是一个依赖于 Web 的语音助手，你可以通过 Azure 或 Openai 的识别服务在小型设备上轻松地运行它

- 运行 `BaseEvent` 服务器

```toml
# 基础对话事件服务器，Web支持或者音箱用
[Controller.BaseServer]
port = 9559
```

- 运行 Vits 服务器

https://github.com/LlmKira/MoeGoe

- 运行助手

```shell
cd Assistant
cat install.md
pip3 install -r requirements.txt
python3 clinet.py
```

### 🥕 Add Api Key

使用 `/add_api_key` 命令将 [OpenaiKey](https://beta.openai.com/account/api-keys) 添加到 `Config/api_keys.json`.

### 🫧 About ID

您可能对我们的多平台 ID 系统感到好奇。这我们将您的 ID 存储在我们的 json/数据库中的方式: `real_id` + `suffix`.

- toml

在 `app.toml` 中使用您的真实 ID, 即为没有后缀的白名单.

- json/command

当您使用 用户/组 授权命令时，需要在真实ID后面加上对应的后缀ID.

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

### 关键词过滤配置

为了防范恶意的诱导和攻击，我们有 `Openai TosApi过滤` 和 `简繁关键词过滤` 两种措施。

- 简繁关键词过滤
  如果不存在，敏感词文件会被自动初始化进 `Data/Danger.form`，关闭只需要清空至一行即可。

- Openai TosApi过滤

将审查类型数组留空即可关闭过滤器。

Please see [Service Configuration Guide](https://llmkira.github.io/Docs/guide/service)

### 🌽 `/Config` File

我们的 `llm-kira` 依赖库在没有 Redis 支持的时候，存储在当前包目录下。

程序本身除了 `api_keys.json` `service.json` `assistants.json` 全部存储在 Redis 中以获得稳健性。

如果你有放 `config.json`，程序会自动初始化此文件。且使用 `/config` 命令可以更新配置到此文件。

### 🎸 Command

因为缺乏维护者的原因，部分命令仅在部分平台起效。

```shell
chat - 交谈
write - 续写
forgetme - 重置记忆
remind - 场景设定 取消用短文本覆盖
voice - 启用语音支持
style - 设定偏好词
help - 帮助

trigger - 管理员启动主动回复
trace - 管理员启动关联频道贴文自动追踪
cross - 管理员启动是否交叉回复
silent - 管理员启动报错沉默

auto_adjust - 自动优化器
set_user_cold - 设置用户冷却时间
set_group_cold - 设置群组冷却时间
set_token_limit - 设置输出限制长度
set_input_limit - 设置输入限制长度
see_api_key - 现在几个 Api key
del_api_key - 删除 Api key
add_api_key - 增加 Api key
config - 获取/备份热配置文件
set_per_user_limit - 设置普通用户额度
set_per_hour_limit - 设置用户小时额度
promote_user_limit - 提升用户额度
reset_user_usage - 重置用户额度
add_block_group - 禁止群组
del_block_group - 解禁群组
add_block_user - 禁止用户
del_block_user - 解禁用户
add_white_group - 加入白名单群组
add_white_user - 加入白名单用户
del_white_group - 除名白名单群
del_white_user - 除名白名单人
update_detect - 更新敏感词
open_user_white_mode - 开用户白名单
open_group_white_mode - 开群组白名单
close_user_white_mode - 关用户白名单
close_group_white_mode - 关群组白名单
open - 开启机器人
close - 关闭机器人
change_head - 设定人设开关
change_style - 设定风格开关
```

### 🧀 More Docs

[部署文档](https://llmkira.github.io/Docs/en/guide/getting-started)的详细信息

Network Plugins/Proxy Settings/自定义模型名称/语音服务/图片理解/Censor配置请参见
[服务器配置指南](https://llmkira.github.io/Docs/guide/service)

详细接口/服务配置/自定义 请查看文档 [部署指南](https://llmkira.github.io/Docs/guide/getting-started)

贴纸设置/代理设置/自定义模型名称/语音服务/图片理解/审查配置
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

- ChatGPT Mirai Bot 是一个基于ChatGPT Web Api & Edge Api & GPT3.5 的 QQ 机器人，同样支持多账号轮换负载。

https://github.com/lss233/chatgpt-mirai-qq-bot

## 📃 License

```

This project open source and available under
the [AGPL License](https://github.com/LLMKira/Openaibot/blob/main/LICENSE).

```

[CLAUSE](https://github.com/LlmKira/Openaibot/blob/main/CLAUSE.md) 说明了如何授权，声明，附加条款等内容。

### Fossa

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_large)

> 你不会相信，但是 Ai 也写了这个 Readme 的一部分
