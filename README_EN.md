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
- 🎵 Fine-grained consumption data storage, statistics on plugin credit consumption.
- 🍖 Continuous session design for function plugins

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

## 📦 Deploy

[🧀 Deploy](https://llmkira.github.io/Docs/en/) Docs for more information.

### 🥞 Automatic installation

If you are using a brand new server, you can use the following shell to try to automatically install this project.

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

Tip:If you use Docker to run your robot, you may encounter missing dependencies. Sometimes we forget to package new
dependencies.

## 💻 How to develop?

For plugin development, please refer to the sample plugins in the `plugins` directory.

Plugin development please refer to [🧀 Plugin Dev Docs](https://llmkira.github.io/Docs/en/dev/basic)

## 🤝 We need your help!

We can't do it on our own at the moment:

- [ ] User Auth System
- [ ] Security checks on procedures

Feel free to submit a Pull Request or discuss, we'd love to receive your contribution!

## 📜 Agreement

> This project has no relationship with OPENAI/ChatGpt.


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot.svg?type=small)](https://app.fossa.com/projects/git%2Bgithub.com%2Fsudoskys%2FOpenaibot?ref=badge_small)