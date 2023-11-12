![cover](https://raw.githubusercontent.com/LlmKira/.github/main/llmbot/project_cover.png)

-----------------------

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
  <a href="https://llmkira.github.io/Docs/en">🍩 Deploy Docs</a> 
  &
  <a href="https://llmkira.github.io/Docs/en/dev/basic">🧀 Dev Docs</a>
  &
  <a href="README.md">📝 中文Readme</a>
</p>

> Any issues with deployment? Submit an Issue to help us fix SLA

The project is Open source reproduction attempt for [ChatGpt](https://chatgpt.com) like, with `FunctionCall`
and `ToolCall` as the core,
supporting multiple messaging platforms.

Using message queue, it can easily handle function requests and support complex plug-in and functional design. Well
supported access to file.

Supports multiple model sources and cross-platform message forwarding.

| Demo                              | 
|-----------------------------------|
| ![sticker](./docs/chain_chat.gif) |

Unlike previous projects, this project tries to replicate ChatGpt's plugin system based on the messaging platform,
implementing some or more features.

> Because func call is a feature, it only supports Openai type api, and does not intend to support LLM without func
> call.

## 📦 Feature

- 🍪 Complete plug-in development ecosystem, using classic design, can be used after installation through `pip`
- 📝 Messaging system, no limit on time, no limit on sender, define sender and receiver, completely decoupled logic
- 📎 Route messages, customize message routing, and use routing to determine how to operate.
- 📬 Public open quota/private self-configured backend/proxy token authentication, providing flexible and scalable
  authentication development solutions
- 🍾 Support middleware interception development, and develop extensions to operate data before and after the process
- 🎵 Refined statistics system, easy to count usage
- 🍰 Support plug-in human-in-the-loop verification, authentication, and plug-in blacklist can be set
- 📦 Improve standard file interaction support, upload/download files
- 🍖 Supports individual configuration of environment keys and provides personal private environment variables for
  plug-ins
- 🍟 Supports incremental support for large language models, supports multi-platform expansion, and can be adapted by
  inheriting standard classes
- 🍔 Supports both `FunctionCall` and `ToolCall` features to dynamically build the required function classes based on the
  model

### 🧀 Introduction to authentication system

The authentication system we use is called `Service Provider`, which is the service provider. Its role is to assign
Endpoint/Key/Model to each sender for authentication.
Has a `token` as a bound OpenKey. The program will call the set `Service Provider` to read the private Key/configuration
Token to obtain the authentication information.

![auth](./docs/SeriveProvider.svg)

Both the authentication component and the backend need to be implemented by yourself.

### 🧀 Preview of some plugins

| Sticker Converter                   | Timer Func                      | Translate                                    |
|-------------------------------------|---------------------------------|----------------------------------------------|
| ![sticker](./docs/sticker_func.gif) | ![timer](./docs/timer_func.gif) | ![translate](./docs/translate_file_func.gif) |

### 🎬 Platform support

| Platform | Support | File System | Tip                        |
|----------|---------|-------------|----------------------------|
| Telegram | ✅       | ✅           |                            |
| Discord  | ✅       | ✅           |                            |
| Kook     | ✅       | ✅           | No Support `Replies start` |
| Slack    | ✅       | ✅           | No Support `Replies start` |
| QQ       | ❌       |             |                            |
| Wechat   | ❌       |             |                            |
| Twitter  | ❌       |             |                            |
| Matrix   | ❌       |             |                            |
| IRC      | ❌       |             |                            |
| ...      |         |             | Create issue/pr            |

## 📦 Quick Start

Read the [🧀 Deployment Documentation](https://llmkira.github.io/Docs/) for more information.

Please use `python3 start_sender.py` `python3 start_receiver.py` to test whether it can run normally.

#### Performance indicator test (Until 2023/11/1)

Attention, does not include the memory usage of services such as pm2, redis, rabbitmq, mongodb, docker, etc.

| Process    | Memory Max Head Size | Tester                                           | Client   |
|------------|----------------------|--------------------------------------------------|----------|
| `receiver` | 120.847MB            | `python3 -m memray run --live start_receiver.py` | telegram |
| `sender`   | 83.669MB             | `python3 -m memray run --live start_sender.py`   | telegram |

### 🥣 Docker

Build Hub: [sudoskys/llmbot](https://hub.docker.com/repository/docker/sudoskys/llmbot/general)

#### Automatic Docker/Docker-compose installation

If you are using a brand new server, you can use the following shell to try to automatically install this project.

This script will automatically install the required services and map ports using Docker methods, if you have
deployed `redis`, `rabbitmq`, `mongodb`.

Please modify the `docker-compose.yml` file yourself.

```shell

curl -sSL https://raw.githubusercontent.com/LLMKira/Openaibot/main/deploy.sh | bash
```

#### Manual Docker-compose installation

```shell
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
pip install poetry && poetry install --all-extras
docker-compose -f docker-compose.yml up -d

```

Update the image with `docker-compose pull`.

View Shell in docker, use `docker exec -it llmbot /bin/bash`, type `exit` to exit.

### 🍔 Shell

To manually start using Pm2, you need to install `redis`, `rabbitmq`, `mongodb` by yourself.

```shell
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
pip install poetry && poetry install --all-extras
apt install npm -y && npm install pm2 && pm2 start pm2.json
pm2 monit

```

Use `pm2 restart pm2.json` to restart the program.

> Recommend using `poetry` for dependency management, because we use `pydantic^1.9.0`, in order to prevent version
> conflicts, we use `poetry` for dependency management.

## 🍪 Slash Command

```shell
clear - erase chat history
help - show docs
chat - chat
task - chat with function_enable
ask - chat with function_disable
tool - list all functions
set_endpoint - set private key and endpoint
clear_endpoint - erase private key and endpoint
auth - auth a function
env - env for function
token - bind token
token_clear - clear token binding
func_ban - ban a function
func_unban - unban a function
bind - Bind rss platforms
unbind - Unbind rss platforms
```

## 💻 How to develop?

For plugin development, please refer to the sample plugins in the `plugins` directory.

Plugin development please refer to [🧀 Plugin Dev Docs](https://llmkira.github.io/Docs/en/dev/basic)

## 🤝 We need your help!

This is a long term project and we started the development of the LLM APP very early!

We applied a plugin-like system and search online before GPT3 OpenaiApi was released(davinci-003)

After many iterations, we have worked hard to make this project more standardized, generic, and open.

We can't do it on our own at the moment:

- [ ] We need help with the documentation
- [ ] Web UI

Feel free to submit a Pull Request or discuss, we'd love to receive your contribution!

## 📜 Agreement

> This project has no relationship with OPENAI/ChatGpt.


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)