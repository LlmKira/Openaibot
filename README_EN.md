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


LLMBot is a message queue based IM Bot developed around the concept of an intelligent robot assistant that can be loaded
with plugins to perform many functions. Implemented with Openai's new Feature `gpt-function-call`
support.

| Demo                              | 
|-----------------------------------|
| ![sticker](./docs/chain_chat.gif) |

Unlike previous projects, this project tries to replicate ChatGpt's plugin system based on the messaging platform,
implementing some or more features.

> Because func call is a feature, it only supports Openai type api, and does not intend to support LLM without func
> call.

## 📦 Feature

- 🍪 Call a number of pre-defined functions in natural language, use `pip` install every plugin you need.
- 📝 Messaging system, define send receivers and data can be delivered to the llm chain.
- 📎 Subscription system, which can subscribe to multiple senders in addition to paired senders, with push functionality.
- 📦 Non-question-and-answer binding, unlimited time and unlimited sender triggered response.
- 📬 Customizable ApiKey and Endpoint, traceability of sender authentication info.
- 🍾 Easy Interactive Experience.
- 🍖 Continuous session design for function plug-ins, blacklist design
- 🍟 Support for plug-in human-in-the-loop authentication, support for plug-in atomic singleton configuration, support
  for development of pre-message text validation Hooks, support for development of text<->media converters, support for
  error disabling Hooks

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
pip install -r requirements.txt
docker-compose -f docker-compose.yml up -d

```

### 🍔 Shell

To manually start using Pm2, you need to install `redis`, `rabbitmq`, `mongodb` by yourself.

```shell
git clone https://github.com/LlmKira/Openaibot.git
cd Openaibot
apt install npm -y && npm install pm2 && pm2 start pm2.json
pm2 monit

```

Use `pm2 restart pm2.json` to restart the program.

## 🍪 Slash Command

```shell
help - help
chat - chat
task - task
ask - question and answer
tool - list of tools
bind - Bind optional platforms
unbind - Unbind optional platforms
clear - delete own records
set_endpoint - Custom backend
clear_endpoint - Erase custom settings
auth - authentication
env - virtual environment settings
token - bind token
token_clear - clear token
func_ban - disable function
func_unban - unban function
```

## 💻 How to develop?

For plugin development, please refer to the sample plugins in the `plugins` directory.

Plugin development please refer to [🧀 Plugin Dev Docs](https://llmkira.github.io/Docs/en/dev/basic)

## 🤝 We need your help!

We can't do it on our own at the moment:

- [ ] We need help with the documentation
- [ ] Web UI

Feel free to submit a Pull Request or discuss, we'd love to receive your contribution!

## 📜 Agreement

> This project has no relationship with OPENAI/ChatGpt.


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)