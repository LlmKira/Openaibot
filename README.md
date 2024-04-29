![cover](https://raw.githubusercontent.com/LlmKira/.github/main/llmbot/project_cover.png)

------------------

<p align="center">
<a href="https://hub.docker.com/repository/docker/sudoskys/llmbot/general">
    <img src="https://img.shields.io/docker/pulls/sudoskys/llmbot" alt="docker">
</a>
<a href="https://badge.fury.io/py/llmkira">
    <img src="https://badge.fury.io/py/llmkira.svg" alt="docker workflow">
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
  <a href="https://llmkira.github.io/Docs/">🍩 Deploy Docs</a>
  &
  <a href="https://llmkira.github.io/Docs/dev/basic">🧀 Dev Docs</a>
  &
  <a href=".github/CONTRIBUTING.md">🤝 Contribute</a>
</p>

> Don't hesitate to Star ⭐️, Issue 📝, and PR 🛠️

> Python>=3.9

This project uses the ToolCall feature.

It integrates a message queuing and snapshot system, offering plugin mechanisms and authentication prior to plugin
execution.

The bot adheres to the **Openai Format Schema**. Please adapt using [gateway](https://github.com/Portkey-AI/gateway)
or [one-api](https://github.com/songquanpeng/one-api) independently.

| Demo                                                                          | Vision With Voice                                                        | Code Interpreter                                                                      |
|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| ![sticker](https://github.com/LlmKira/Openaibot/raw/main/docs/chain_chat.gif) | ![vision](https://github.com/LlmKira/Openaibot/raw/main/docs/vision.gif) | ![code](https://github.com/LlmKira/Openaibot/raw/main/docs/code_interpreter_func.gif) |

## 🔨 Roadmap

> The program has iterated to its fourth generation.

- [x] Removal of legacy code
- [x] Deletion of metric system
- [x] Deletion of model selection system, unified to OpenAI Schema
- [x] Implementation of a more robust plugin system
- [x] Project structure simplification
- [x] Elimination of the Provider system
- [x] Hook support
- [x] Access to TTS
- [x] Add standalone support for gpt-4-turbo and vision
- [ ] Add LLM reference support to the plugin environment. (extract && search in text)

## 📦 Features

- 🍪 A comprehensive plugin development ecosystem, adopting a classic design, and seamless integration with plugins
  through `pip` installation
- 📝 Message system with no time or sender constraints, offering fully decoupled logics
- 📬 Offers Login via a URL mechanism, providing a flexible and expandable authentication development solution
- 🍰 Empowers users to authorize plugin execution. Users can configure plugin environment variables at their discretion
- 📦 Support for plugins to access files
- 🍟 Multi-platform support – extend new platforms by inheriting the base class
- 🍔 Plugins can determine their appearance in new sessions dynamically, preventing performance degradation despite large
  amounts of plugins

### 🍔 Login Modes

- `Login via url`: Use `/login <a token>$<something like https://provider.com/login>` to Login. The program posts the token to the interface to
  retrieve configuration
  information, [how to develop this](https://github.com/LlmKira/Openaibot/blob/81eddbff0f136697d5ad6e13ee1a7477b26624ed/app/components/credential.py#L20).
- `Login`: Use `/login https://<api endpoint>/v1$<api key>$<the model>$<tool model such as gpt-3.5-turbo>` to login

### 🧀 Plugin Can Do More

| Sticker Converter                   | Timer Function(built-in)        |
|-------------------------------------|---------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) |

### 🎬 Platform Support

| Platform | Support | File System | Remarks                                |
|----------|---------|-------------|----------------------------------------|
| Telegram | ✅       | ✅           |                                        |
| Discord  | ✅       | ✅           |                                        |
| Kook     | ✅       | ✅           | Does not support `triggering by reply` |
| Slack    | ✅       | ✅           | Does not support `triggering by reply` |
| Line     | ❌       |             |                                        |
| QQ       | ❌       |             |                                        |
| Wechat   | ❌       |             |                                        |
| Twitter  | ❌       |             |                                        |
| Matrix   | ❌       |             |                                        |
| IRC      | ❌       |             |                                        |
| ...      |         |             | Create Issue/PR                        |

## 📦 Quick Start

Refer to the [🧀 Deployment Document](https://llmkira.github.io/Docs/) for more information.

### 📦 One-click Deployment

If you are using a brand-new server, you can use the following shell to automatically install this project.

```shell
curl -sSL https://raw.githubusercontent.com/LLMKira/Openaibot/main/deploy.sh | bash
```

### 📦 Manual Installation

```shell
# Install Voice dependencies
apt install ffmpeg
# Install RabbitMQ
docker pull rabbitmq:3.10-management
docker run -d -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=8a8a8a \
  --hostname myRabbit \
  --name rabbitmq \
  rabbitmq:3.10-management
docker ps -l
# Install Project
git clone https://github.com/LlmKira/Openaibot/
cd Openaibot
pip install pdm
pdm install -G bot
cp .env.exp .env && nano .env
# Test
pdm run python3 start_sender.py
pdm run python3 start_receiver.py
# Host
apt install npm
npm install pm2 -g
pm2 start pm2.json
```

> **Be sure to change the default password for the command, or disable open ports to prevent the database from being
scanned and attacked.**

### 🥣 Docker

Build Hub: [sudoskys/llmbot](https://hub.docker.com/repository/docker/sudoskys/llmbot/general)

> Note that if you run this project using Docker, you will start Redis, MongoDB, and RabbitMQ. But if you're running
> locally, just RabbitMQ

#### Manual Docker-compose Installation

```shell
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
cp .env.exp .env&&nano .env
docker-compose -f docker-compose.yml up -d
```

The Docker configuration file `docker-compose.yml` contains all databases. In fact, Redis and MongoDB are not required.
You can remove these databases yourself and use the local file system.

Update image using `docker-compose pull`.

Use `docker exec -it llmbot /bin/bash` to view Shell in Docker, enter `exit` to exit.

## 🍪 Slash Commands

```shell
clear - Deletes chat records
login - Login to the bot
help - Displays documentation
chat - Conversation
task - Use a function to converse
ask - Disable function-based conversations
tool - Lists all functions
auth - Authorize a function
env - Environment variables of the function
learn - Learn your instructions, /learn reset to clear
```

## 💻 How to Develop Plugins?

Refer to the example plugins in the `plugins` directory and
the [🧀 Plugin Development Document](https://llmkira.github.io/Docs/dev/basic) for plugin development documentation.

### Hooks

Hooks control the EventMessage in sender and receiver. For example, we have `voice_hook` in built-in hooks.

you can enable it by setting `VOICE_REPLY_ME=true` in `.env`.

```shell
/env VOICE_REPLY_ME=yes
# must

/env REECHO_VOICE_KEY=<key in dev.reecho.ai>
# not must
```

use `/env VOICE_REPLY_ME=NONE` to disable this env.

check the source code in `llmkira/extra/voice_hook.py`, learn to write your own hooks.

## 🧀 Sponsor

[![sponsor](./.github/sponsor_ohmygpt.png)](https://www.ohmygpt.com)

## 📜 Notice

> This project, named OpenAiBot, signifying "Open Artificial Intelligence Robot", is not officially affiliated with
> OpenAI.


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)
