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

The model adheres to the Openai Schema, other models are not supported. Please adapt using gateways independently.

| Demo                              |
|-----------------------------------|
| ![sticker](./docs/chain_chat.gif) |

## 🍔 Roadmap

- [x] Removal of legacy code
- [x] Deletion of metric system
- [x] Deletion of model selection system, unified to OpenAI Schema
- [x] Implementation of a more robust plugin system
- [x] Project structure simplification
- [x] Elimination of the Provider system

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

- `Login via url`: Use `/login token#https://provider.com` to Login. The program posts the token to the interface to
  retrieve configuration information
- `Login`: Use `/login https://api.com/v1#key#model` to login

### 🧀 Plugin Previews

| Sticker Converter                   | Timer Function                  | Translate Function                           |
|-------------------------------------|---------------------------------|----------------------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) | ![translate](./docs/translate_file_func.gif) |

### 🎬 Platform Support

| Platform | Support | File System | Remarks                                |
|----------|---------|-------------|----------------------------------------|
| Telegram | ✅       | ✅           |                                        |
| Discord  | ✅       | ✅           |                                        |
| Kook     | ✅       | ✅           | Does not support `triggering by reply` |
| Slack    | ✅       | ✅           | Does not support `triggering by reply` |
| QQ       | ❌       |             |                                        |
| Wechat   | ❌       |             |                                        |
| Twitter  | ❌       |             |                                        |
| Matrix   | ❌       |             |                                        |
| IRC      | ❌       |             |                                        |
| ...      |         |             | Create Issue/PR                        |

## 📦 Quick Start

Refer to the [🧀 Deployment Document](https://llmkira.github.io/Docs/) for more information.

```shell
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
pip install pdm
pdm install -G bot
cp .env.exp .env && nano .env
# Test
pdm run python3 start_sender.py
pdm run python3 start_receiver.py
# Host
pdm start pm2.json
```

### 🥣 Docker

Build Hub: [sudoskys/llmbot](https://hub.docker.com/repository/docker/sudoskys/llmbot/general)

#### Automatic Docker/Docker-compose Installation

If you are using a brand new server, you can use the following shell to automatically install this project.

This script automatically installs the required services and maps ports using Docker methods. If you have
deployed `redis`, `rabbitmq`, `mongodb`, please modify the `docker-compose.yml` file accordingly.

```shell
curl -sSL https://raw.githubusercontent.com/LLMKira/Openaibot/main/deploy.sh | bash
```

#### Manual Docker-compose Installation

```shell
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
cp .env.exp .env&&nano .env
docker-compose -f docker-compose.yml up -d
```

Update image using `docker-compose pull`.

Use `docker exec -it llmbot /bin/bash` to view Shell in Docker, enter `exit` to exit.

## 🍪 Slash Commands

```shell
clear - Deletes chat records
help - Displays documentation
chat - Conversation
task - Use a function to converse
ask - Disable function-based conversations
tool - Lists all functions
login - Login
auth - Authorize a function
env - Environment variables of the function
```

## 💻 How to Develop Plugins?

Refer to the example plugins in the `plugins` directory and
the [🧀 Plugin Development Document](https://llmkira.github.io/Docs/dev/basic) for plugin development documentation.

## 🧀 Sponsor

[![sponsor](./.github/sponsor_ohmygpt.png)](https://www.ohmygpt.com)

## 📜 Notice

> This project, named OpenAiBot, signifying "Open Artificial Intelligence Robot", is not officially affiliated with
> OpenAI.


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)
