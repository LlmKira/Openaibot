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

LLMBot 是基于消息队列，围绕智能机器人助理概念开发的 IM Bot，可以装载插件完成许多功能。由 Openai 的新
Feature `gpt-function-call`
支持实现。

| Demo                              |
|-----------------------------------| 
| ![sticker](./docs/chain_chat.gif) | 

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
- 🍟 插件系统的密钥组件，中间件组件，插件版本兼容管理

### 🧀 部分插件预览

| Sticker Converter                   | Timer Func                      | Translate Func                               |
|-------------------------------------|---------------------------------|----------------------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) | ![translate](./docs/translate_file_func.gif) |

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

> 我经常忘记打包依赖，按照文档运行失败，请直接提交 Issue

### 🥞 自动安装

如果你在使用一台崭新的服务器，你可以使用下面的Shell来尝试自动安装本项目。

```shell

curl -sSL https://raw.githubusercontent.com/LLMKira/Openaibot/main/deploy.sh | bash
```

### 🥣 Docker

Build Hub: [sudoskys/llmbot](https://hub.docker.com/repository/docker/sudoskys/llmbot/general)

```shell

git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
docker-compose -f docker-compose.yml -p llmbot up -d llmbot
```

注意，如果您使用 Docker 运行机器人，您可能会遇到依赖缺失问题，有时候我们会忘记打包新的依赖库。

## 💻 如何开发插件？

插件开发文档请参考 `plugins` 目录下的示例插件和 [🧀 插件开发文档](https://llmkira.github.io/Docs/dev/basic)

## 🤝 We need your help!

We can't do it on our own at the moment:

- [ ] User Auth System
- [ ] Security checks on procedures

Feel free to submit a Pull Request or discuss, we'd love to receive your contribution!

## 📜 告知

> 此项目与 Openai 官方无关，全称为 OpenAiBot，表示开放人工智能机器人，并不表示为 Openai 所属机器人。

> 如果您所在辖区禁止使用 Openai 服务，请勿使用此项目。

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)