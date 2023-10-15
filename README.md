![cover](https://raw.githubusercontent.com/LlmKira/.github/main/llmbot/project_cover.png)

[![Docker Image Size (tag)](https://img.shields.io/badge/Docker-Image-blue)](https://hub.docker.com/repository/docker/sudoskys/llmbot/general)
![Docker Image Version (latest semver)](https://img.shields.io/docker/v/sudoskys/llmbot)

![docker workflow](https://github.com/llmkira/openaibot/actions/workflows/docker-ci.yaml/badge.svg)
[![Package](https://github.com/LlmKira/Openaibot/actions/workflows/publish.yml/badge.svg)](https://github.com/LlmKira/Openaibot/actions/workflows/publish.yml)

[![Telegram](https://img.shields.io/badge/Join-Telegram-blue)](https://t.me/Openai_LLM)
[![Discord](https://img.shields.io/badge/Join-Discord-blue)](https://discord.gg/6QHNdwhdE5)

[English Readme](README_EN.md)

[🧀 插件开发文档](https://llmkira.github.io/Docs/plugin/basic)

LLMBot 是基于消息队列，围绕智能机器人助理概念开发的 IM Bot，可以装载插件完成许多功能。由 Openai 的新
Feature `gpt-function-call`
支持实现。

| Demo                              |
|-----------------------------------|
| ![sticker](./docs/chain_chat.gif) | ![timer](./docs/timer_func.gif) |

与之前的项目不同的是，此项目尝试基于消息平台复刻 ChatGpt 的插件系统，实现部分或更进一步的功能。

> 因为 func call 为 feature,所以只支持 Openai 类型的 api, 不打算支持没有 func call 的 LLM

## 📦 Feature

- 🍪 通过自然语言调用若干预先定义好的功能函数
- 📝 消息系统，定义发送接收端和数据即可递送至链中
- 📎 订阅系统，可以订阅除了结对发送者外的多个发送者，兼具推送功能
- 📦 非问答绑定，不限时间不限发送端触发回复
- 📬 自定义 ApiKey 和 后端，追溯发送者的鉴权信息
- 🍾 简洁交互设计
- 🎵 细化的消费数据存储，统计插件的额度消耗情况，全场景追溯消费记录产生
- 🍰 自带联网插件实现
- 📦 文件交互支持
- 🍖 对函数插件的连续会话设计

### 🧀 部分插件预览

| Sticker Converter                   | Timer Func                      | Translate Func                               |
|-------------------------------------|---------------------------------|----------------------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) | ![translate](./docs/translate_file_func.gif) |

### 🎬 平台支持

| 平台       | 支持情况 | 备注 |
|----------|------|----|
| Telegram | ✅    |    |
| Discord  | ❌    |    |
| QQ       | ❌    |    |
| Wechat   | ❌    |    |
| Twitter  | ❌    |    |

```python3
__plugin_name__ = "set_alarm_reminder"

alarm = Function(name=__plugin_name__, description="Set a timed reminder")
alarm.add_property(
    property_name="delay",
    property_description="The delay time, in minutes",
    property_type="integer",
    required=True
)
alarm.add_property(
    property_name="content",
    property_description="reminder content",
    property_type="string",
    required=True
)
```

## 📝 部署指南

请确认您的系统为UTF8，`dpkg-reconfigure locales`

请确认您服务器的内存大于 `1G`,否则使用 PM2 会无限重启。

如果你在使用一台崭新的服务器，你可以使用下面的Shell来尝试自动安装本项目。

```shell
curl -sSL https://raw.githubusercontent.com/LLMKira/Openaibot/main/deploy.sh | bash

```

### 🌻 配置

- (可选) 解决冲突

`pip uninstall llm-kira`

- 🛠 配置 `.env` 文件

```bash
cp .env.example .env
nano .env

```

- 克隆项目

```bash
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
pip install -r requirements.txt

```

- ⚙️ 安装依赖

```bash
pip install -r requirements.txt
```

- 🗄 配置数据库环境

```bash
# 安装 Redis
apt-get install redis
systemctl enable redis.service --now
```

```bash
# 安装 RabbitMQ
docker pull rabbitmq:3.10-management
docker run -d -p 5672:5672 -p 15672:15672 \
        -e RABBITMQ_DEFAULT_USER=admin \
        -e RABBITMQ_DEFAULT_PASS=admin \
        --hostname myRabbit \
        --name rabbitmq \
        rabbitmq:3.10-management 
docker ps -l
```  

## ▶️ 运行

### Docker

```shell
cd Openaibot
docker-compose -f docker-compose.yml -p llmbot up -d llmbot --compatibility

```

安装 Docker 可以参考 [官方文档](https://docs.docker.com/engine/install/ubuntu/)

安装 Docker Compose 可以参考 [官方文档](https://docs.docker.com/compose/install/)

或者 [博客文章](https://krau.top/posts/install-docker-one-key)

Windows 用户可以安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### PM2

````
apt install npm
npm install pm2 -g
pm2 start pm2.json
````

### Shell

```bash
python3 start_sender.py
python3 start_receiver.py

```

## 基础命令

```shell
help - 帮助
chat - 聊天
task - 任务
tool - 工具列表
bind - 绑定可选平台
unbind - 解绑可选平台
clear - 删除自己的记录
rset_endpoint - 自定义后端
rset_key - 设置openai
clear_rset - 抹除自定义设置
auth - 鉴权

```

### 🥽 环境变量

| 变量名称                | 值     | 说明                       |
|---------------------|-------|--------------------------|
| `LLMBOT_STOP_REPLY` | 1     | 如果值为 1，则停止接收回复           |
| `LLMBOT_LOG_OUTPUT` | DEBUG | 如果值为 DEBUG，则在屏幕上打印长调试日志。 |

## 💻 如何开发插件？

插件开发请参考 `plugins` 目录下的示例插件。

插件开发文档请参考 [🧀 插件开发文档](https://llmkira.github.io/Docs/plugin/basic)

## 🤝 We need your help!

We can't do it on our own at the moment:

- [ ] Security checks on procedures
- [ ] User Auth System

Feel free to submit a Pull Request or discuss, we'd love to receive your contribution!

