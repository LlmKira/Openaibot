# LLMBot

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/sudoskys/llmbot/latest)
![Docker Image Version (latest semver)](https://img.shields.io/docker/v/sudoskys/llmbot)
![docker workflow](https://github.com/llmkira/llmbot/actions/workflows/docker-ci.yaml/badge.svg)

LLMBot is a message queue based bot helper that can be loaded with plugins to perform many functions. Validation project
for the Gpt Func Call and Broadcast mechanisms.

Unlike the `OpenaiBot` project, this project tries to replicate ChatGpt's plugin system based on a messaging platform.
Implement some or more features.

Most of the functionality of this project can be done by plugins.

> Because func call is a feature, it only supports Openai type api, not LLM without func call.

## 📦 Feature

- 📦 middleware/plugin system, can be freely extended.
- 📝 Messaging system, free from platform and time constraints
- 📎 Subscription system, can subscribe to multiple senders
- 📬 Customized ApiKey and backend
- 🍾 Simple interaction design to avoid cumbersome permission validation
- 🎵 Fine-grained consumption records
- 🍰 Networking plugin implementation

### 🧀 Preview of some plugins

| Sticker Converter                     | Timer Func                        |
|---------------------------------------|-----------------------------------|
| ! [sticker](. /docs/sticker_func.gif) | ! [timer](. /docs/timer_func.gif) | !

## 📝 Deployment Guide

Make sure your system is UTF8, `dpkg-reconfigure locales`

### Docker

```shell
docker-compose -f docker-compose.yml -p llmbot up -d llmbot --compatibility
```

### PM2

````
apt install npm
npm install pm2 -g
pm2 start pm2.json
````

### Shell

- (Optional) Resolving conflicts

  `pip uninstall llm-kira`

- 🛠 Configure the `.env` file

```bash
cp .env.example .env
```

- ⚙️ Install dependencies

```bash
pip install -r requirements.txt
```

- 🗄 Configure the database environment

```bash
# Install Redis
apt-get install redis
systemctl enable redis.service --now
```

```bash
# Install RabbitMQ
docker pull rabbitmq:3.10-management
docker run -d -p 5672:5672 -p 15672:15672 \
        -e RABBITMQ_DEFAULT_USER=admin \
        -e RABBITMQ_DEFAULT_PASS=admin \
        --hostname myRabbit \
        --name rabbitmq \
        rabbitmq:3.10-management 
docker ps -l
```  

- ▶️ Run

```bash
python3 start_sender.py
python3 start_receiver.py

```

## Basic commands

```shell
help - help
chat - chat
task - task
tool - tool list
bind - bind optional platforms
unbind - unbind optional platforms
clear - Delete your own records
rset_endpoint - customize the backend
rset_key - set openai
clear_rset - wipe custom settings

```

## 💻 How to develop?

For plugin development, please refer to the sample plugins in the `plugins` directory.

## 🤝 How can I contribute?

Feel free to submit a Pull Request, we'd love to receive your contribution! Please make sure your code conforms to our
code specification and include a detailed description. Thank you for your support and contribution! 😊😊