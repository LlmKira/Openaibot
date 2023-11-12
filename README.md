![cover](https://raw.githubusercontent.com/LlmKira/.github/main/llmbot/project_cover.png)

------------------

<p align="center">
<a href="https://hub.docker.com/repository/docker/sudoskys/llmbot/general">
    <img src="https://img.shields.io/docker/pulls/sudoskys/llmbot" alt="docker">
</a>
<a href="https://github.com/llmkira/openaibot/actions/workflows/docker-ci.yaml">
    <img src="https://github.com/llmkira/openaibot/actions/workflows/docker-ci.yaml/badge.svg" alt="docker workflow">
</a>
<br />
<a href="https://t.me/Openai_LLM">
    <img src="https://img.shields.io/badge/Join-Telegram-blue" alt="telegram">
</a>
<a href="https://discord.gg/6QHNdwhdE5">
    <img src="https://img.shields.io/badge/Join-Discord-blue" alt="discord">
</a>
<br/>
<a href="https://raw.githubusercontent.com/llmkira/openaibot/main/LICENSE">
    <img src="https://img.shields.io/github/license/llmkira/openaibot" alt="license">
</a>
<a href="https://hub.docker.com/repository/docker/sudoskys/llmbot/builds">
    <img src="https://img.shields.io/docker/v/sudoskys/llmbot" alt="docker build">
</a>
</p>

<p align="center">
  <a href="https://llmkira.github.io/Docs/">🍩 部署文档</a> 
  &
  <a href="https://llmkira.github.io/Docs/dev/basic">🧀 开发文档</a>
  &
  <a href="README_EN.md">📝 English Readme</a>
</p>


> **Look for English README? Click [here](README_EN.md). We also have English
documentation [here](https://llmkira.github.io/Docs/en).**

> 部署遇到问题？提交 Issue 帮助我们提升可用性

此项目为自部署，实用可扩展的机器人核心，以 `FunctionCall` `ToolCall` 为核心，支持多种消息平台。

采用消息队列，很好处理函数请求，支持繁杂的插件和功能设计。良好支持文件系统。

支持多种模型源，支持跨平台消息转发。

| Demo                              |
|-----------------------------------| 
| ![sticker](./docs/chain_chat.gif) | 

与之前的项目不同的是，此项目尝试基于消息平台复刻 ChatGpt 的插件系统，实现部分或更进一步的功能。

> 因为 func call 为 feature,所以只支持 Openai 类型的 api, 不打算支持没有 func call 的 LLM

## 📦 Feature

- 🍪 完善的插件开发生态，采用经典设计，通过 `pip` 安装即可使用
- 📝 消息系统，不限时间，不限发送端，定义发送接收者，逻辑完全解耦
- 📎 路由消息，自定义消息路由，以路由决定运作方式
- 📬 公共开放限额/私人自配置后端/代理Token认证，提供灵活可扩展的鉴权开发方案
- 🍾 支持中间件拦截开发，开发扩展即可操作流程前后数据
- 🎵 细化的统计系统，轻松统计使用情况
- 🍰 支持插件人在回路验证，可鉴权，可设置插件黑名单
- 📦 完善标准的文件交互支持，上传/下载文件
- 🍖 支持个人单独配置环境密钥，为插件提供个人的私有环境变量
- 🍟 支持大语言模型增量支持，支持多平台扩展，继承标准类即可适配
- 🍔 同时支持 `FunctionCall` `ToolCall` 特性，根据模型动态构建需要的函数类

### 🧀 部分插件预览

| Sticker Converter                   | Timer Func                      | Translate Func                               |
|-------------------------------------|---------------------------------|----------------------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) | ![translate](./docs/translate_file_func.gif) |

### 🧀 认证系统介绍

我们采用的认证系统称为 `Service Provider`，即服务提供商，它的作用是为每个发送者分配 Endpoint/Key/Model ，用于鉴权。
拥有一个 `token` 作为绑定的 OpenKey。程序会调用设定的 `Service Provider` 读取私有 Key/配置 Token 来获取鉴权信息。

![auth](./docs/SeriveProvider.svg)

认证组件和后端均需要自行实现。

### 🎬 平台支持

| 平台       | 支持情况 | 文件系统 | 备注          |
|----------|------|------|-------------|
| Telegram | ✅    | ✅    |             |
| Discord  | ✅    | ✅    |             |
| Kook     | ✅    | ✅    | 不支持 `被回复启动` |
| Slack    | ✅    | ✅    | 不支持 `被回复启动` |
| QQ       | ❌    |      |             |
| Wechat   | ❌    |      |             |
| Twitter  | ❌    |      |             |
| Matrix   | ❌    |      |             |
| IRC      | ❌    |      |             |
| ...      |      |      | 创建Issue/PR  |

## 📦 快速开始

阅读 [🧀 部署文档](https://llmkira.github.io/Docs/) 获得更多信息。

请提前用 `python3 start_sender.py`  `python3 start_receiver.py` 测试是否能正常运行。

#### 性能指标测试(Until 2023/11/1)

注意，不包括pm2，redis，rabbitmq，mongodb，docker等服务的内存占用。

| 进程         | 内存均值      | 测算命令                                             | client   |
|------------|-----------|--------------------------------------------------|----------|
| `receiver` | 120.202MB | `python3 -m memray run --live start_receiver.py` | telegram |
| `sender`   | 83.375MB  | `python3 -m memray run --live start_sender.py`   | telegram |

### 🥣 Docker

Build Hub: [sudoskys/llmbot](https://hub.docker.com/repository/docker/sudoskys/llmbot/general)

#### 自动 Docker/Docker-compose安装

如果你在使用一台崭新的服务器，你可以使用下面的Shell来尝试自动安装本项目。

此脚本会自动使用 Docker 方法安装所需服务并映射端口，如果您已经部署了 `redis` ，`rabbitmq` ，`mongodb` 。

请自行修改 `docker-compose.yml` 文件。

```shell

curl -sSL https://raw.githubusercontent.com/LLMKira/Openaibot/main/deploy.sh | bash
```

#### 手动 Docker-compose安装

```shell
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
cp .env.exp .env&&nano .env
docker-compose -f docker-compose.yml up -d

```


更新镜像使用 `docker-compose pull`。

在 docker 中查看 Shell，使用 `docker exec -it llmbot /bin/bash`，输入 `exit` 退出。


### 🍔 Shell

人工使用Pm2启动，需要自行安装 `redis` ，`rabbitmq` ，`mongodb` 。

```shell
git clone https://github.com/LlmKira/Openaibot.git
pip install poetry
cd Openaibot
poetry install --all-extras
cp .env.exp .env&&nano .env
apt install npm -y && npm install pm2 && pm2 start pm2.json
pm2 monit

```

重启程序使用 `pm2 restart pm2.json` 。

> 推荐使用 `poetry` 进行依赖管理，因为我们使用了 `pydantic^1.9.0`，为了防止出现版本冲突，我们使用了 `poetry` 进行依赖管理。

## 🍪 Slash Command

```shell
clear - 删除聊天记录
help - 显示文档
chat - 对话
task - 启用函数以对话
ask - 禁止函数以对话
tool - 列出所有函数
set_endpoint - 设置私有 key 和 endpoint
clear_endpoint - 清除私有 key 和 endpoint
auth - 授权一个函数
env - 函数环境变量
token - 绑定令牌
token_clear - 清除令牌绑定
func_ban - 禁用一个函数
func_unban - 解禁一个函数
bind - 绑定消息源
unbind - 解绑消息源
```

## 💻 如何开发插件？

插件开发文档请参考 `plugins` 目录下的示例插件和 [🧀 插件开发文档](https://llmkira.github.io/Docs/dev/basic)

## 🤝 We need your help!

This is a long term project and we started the development of the LLM APP very early!

We applied a plugin-like system and search online before GPT3 OpenaiApi was released(davinci-003)

After many iterations, we have worked hard to make this project more standardized, generic, and open.

We can't do it on our own at the moment:

- [ ] We need help with the documentation
- [ ] Web UI

Feel free to submit a Pull Request or discuss, we'd love to receive your contribution!

## 📜 告知

> 此项目与 Openai 官方无关，全称为 OpenAiBot，表示开放人工智能机器人，并不表示为 Openai 所属机器人。

> 如果您所在辖区禁止使用 Openai 服务，请勿使用此项目。

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)